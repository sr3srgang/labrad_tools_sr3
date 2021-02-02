from datetime import date, timedelta
from itertools import chain
import json
import os
import time

from device_server.device import DefaultDevice
from sequencer.devices.yesr_sequencer_board.helpers import time_to_ticks
#from sequencer.devices.yesr_sequencer_board.helpers import combine_sequences
from ok_server.proxy import OKProxy


class YeSrSequencerBoard(DefaultDevice):
    sequencer_type = None
    
    ok_servername = None
    ok_interface = None
    ok_bitfilename = None

    conductor_servername = None

    channels = None
        
    mode_wire = 0x00
    sequence_pipe = 0x80
    clk = 50e6 # [Hz]
    
    sequence_directory = '/home/srgang/K/data/sequences/{}/'
    subsequence_names = None
    sequence = None
    raw_sequene = None
    is_master = False
    master_channel = 'Trigger@D15'
    run_priority = 0

    loading = False
    running = False
    sequence = None
    sequence_bytes = None
    max_sequence_bytes = 24000

    def initialize(self, config):
        for key, value in config.items():
            setattr(self, key, value)

        for channel in self.channels:
            channel.set_board(self)
        
        self.connect_to_labrad()
        self.ok_server = self.cxn[self.ok_servername]
        ok = OKProxy(self.ok_server)
        
        fp = ok.okCFrontPanel()
        fp.OpenBySerial(self.ok_interface)
        fp.ConfigureFPGA(self.ok_bitfilename)
        self.fp = fp
        
        self.update_mode()
        self.update_channel_modes()
        self.update_channel_manual_outputs()
        

    def load_sequence(self, sequencename):
        for i in range(365):
            day = date.today() - timedelta(i)
            sequencepath = self.sequence_directory.format(day.strftime('%Y%m%d')) + sequencename
            if os.path.exists(sequencepath):
                break
        if not os.path.exists(sequencepath):
            print(date.today())
            print(sequencename)
            raise Exception(sequencepath)
        
        with open(sequencepath, 'r') as infile:
            sequence = json.load(infile)
        return sequence

    def save_sequence(self, sequence, sequence_name, tmpdir=True):
        sequence_directory = self.sequence_directory.format(time.strftime('%Y%m%d'))
        if tmpdir:
            sequence_directory = os.path.join(sequence_directory, '.tmp')
        if not os.path.exists(sequence_directory):
            os.makedirs(sequence_directory)
        sequence_path = os.path.join(sequence_directory, sequence_name)
        with open(sequence_path, 'w+') as outfile:
            json.dump(sequence, outfile)

    def get_channel(self, channel_id, suppress_error=False):
        """
        expect 3 possibilities for channel_id.
        1) name -> return channel with that name
        2) @loc -> return channel at that location
        3) name@loc -> first try name, then location
        """
        channel = None

        nameloc = channel_id.split('@') + ['']
        name = nameloc[0]
        loc = nameloc[1]
        if name:
           for c in self.channels:
               if c.name == name:
                   channel = c
        if not channel:
            for c in self.channels:
                if c.loc == loc:
                    channel = c
        if (channel is None) and not suppress_error:
            raise ChannelNotFound(channel_id)
        return channel
    
    def match_sequence_key(self, subsequence, channel):
        subsequence_keys = subsequence.keys()

        for key in subsequence_keys:
            if key == channel.key:
                return key 

        for alt_key in channel.alt_keys:
            print alt_key
            for key in subsequence_keys:
                if key == alt_key:
                    return key
        
        subsequence_names = [key.split('@')[0] for key in subsequence.keys()]
        channel_name = channel.key.split('@')[0]
        for key, name in zip(subsequence_keys, subsequence_names):
            if name == channel_name:
                return key 
        
        subsequence_locs = [(key.split('@') + [''])[1] for key in subsequence.keys()]
        channel_loc = (channel.key.split('@')+ [''])[1]
        for key, loc in zip(subsequence_keys, subsequence_locs):
            if loc == channel_loc:
                return key 

    def update_channel_modes(self):
        """ to be implemented by child class """
   
    def update_channel_manual_outputs(self): 
        """ to be implemented by child class """

    def default_sequence_segment(self, channel, dt):
        """ to be implemented by child class """


    def fix_sequence_keys(self, subsequence_names):
        for subsequence_name in set(subsequence_names):
            subsequence = self.load_sequence(subsequence_name)
            master_channel_subsequence = subsequence[self.master_channel]
            
            for channel in self.channels:
                channel_subsequence = []
                matched_key = self.match_sequence_key(subsequence, channel)
                if matched_key:
                    channel_subsequence = subsequence.pop(matched_key)
                if not channel_subsequence:
                    channel_subsequence = [
                        self.default_sequence_segment(channel, s['dt'])
                            for s in master_channel_subsequence
                        ]
                subsequence.update({channel.key: channel_subsequence})

            subsequence_keys = sorted(subsequence.keys(), key=lambda x: x.split('@')[-1])
            self.save_sequence(subsequence, subsequence_name, False)
    
    def combine_subsequences(self, subsequence_list):
        combined_sequence = {}
        for channel in self.channels:
            channel_sequence = []
            for subsequence in subsequence_list:
                channel_sequence += subsequence[channel.key]
            combined_sequence[channel.key] = channel_sequence
        return combined_sequence
    
    def set_sequence(self, subsequence_names):
        try:
            self._set_sequence(subsequence_names)
        except:
            self.fix_sequence_keys(subsequence_names)
            self._set_sequence(subsequence_names)

    def _set_sequence(self, subsequence_names):
        self.subsequence_names = subsequence_names
        
        subsequence_list = []
        for subsequence_name in subsequence_names:
            subsequence = self.load_sequence(subsequence_name)
            subsequence_list.append(subsequence)

        raw_sequence = self.combine_subsequences(subsequence_list)
        self.set_raw_sequence(raw_sequence)

    def get_sequence(self):
        return self.subsequence_names
   
    def set_raw_sequence(self, raw_sequence):
        self.raw_sequence = raw_sequence
        parameter_names = self.get_sequence_parameter_names(raw_sequence)
        parameter_values = self.get_sequence_parameter_values(parameter_names)
        programmable_sequence = self.substitute_sequence_parameters(raw_sequence, parameter_values)
        sequence_bytes = self.make_sequence_bytes(programmable_sequence)
        if len(sequence_bytes) > self.max_sequence_bytes:
            message = "sequence of {} bytes exceeds maximum length of {} bytes".format(len(sequence_bytes), self.max_sequence_bytes)
            raise Exception(message)
        self.sequence_bytes = sequence_bytes
        
        self.set_loading(True)
        self.fp.WriteToPipeIn(self.sequence_pipe, self.sequence_bytes)
        self.set_loading(False)
    
    def get_raw_sequence(self):
        return self.raw_sequence
    
    def get_sequence_parameter_names(self, x):
        if type(x).__name__ in ['str', 'unicode'] and x[0] == '*':
            return [x]
        elif type(x).__name__ == 'list':
            return set(list(chain.from_iterable([
                self.get_sequence_parameter_names(xx) 
                for xx in x])))
        elif type(x).__name__ == 'dict':
            return set(list(chain.from_iterable([
                self.get_sequence_parameter_names(v) 
                for v in x.values()])))
        else:
            return []

    def get_sequence_parameter_values(self, parameter_names):
        if parameter_names:
            request = {
                parameter_name.replace('*', 'sequencer.'): None
                    for parameter_name in parameter_names
                }
            conductor_server = self.cxn[self.conductor_servername]
            parameter_values_json = conductor_server.get_next_parameter_values(json.dumps(request))
            parameter_values = json.loads(parameter_values_json)
        else:
            parameter_values = {}
        sequence_parameter_values = {
            name.replace('sequencer.', '*'): value 
                for name, value in parameter_values.items()
            }
        return sequence_parameter_values

    def substitute_sequence_parameters(self, x, parameter_values):
        if type(x).__name__ in ['str', 'unicode']:
            if x[0] == '*':
                return parameter_values[x]
            else:
                return x
        elif type(x).__name__ == 'list':
            return [self.substitute_sequence_parameters(xx, parameter_values) for xx in x]
        elif type(x).__name__ == 'dict':
            return {k: self.substitute_sequence_parameters(v, parameter_values) for k, v in x.items()}
        else:
            return x
    
    def make_sequence_bytes(self, sequence):
        """ to be implemented by child class """
    
    def update_mode(self):
        mode_word = 0 | 2 * int(self.loading) | self.running
        self.fp.SetWireInValue(self.mode_wire, mode_word)
        self.fp.UpdateWireIns()

    def set_loading(self, loading):
        if loading is not None:
            self.loading = loading
            self.update_mode()
    
    def get_loading(self):
        return self.running
    
    def set_running(self, running):
        if running is not None:
            self.running = running
            self.update_mode()
    
    def get_running(self):
        return self.running
