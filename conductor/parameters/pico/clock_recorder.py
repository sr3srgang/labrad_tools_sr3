import json
import numpy as np
import os
import time

from twisted.internet.defer import inlineCallbacks

from conductor.parameter import ConductorParameter

class Recorder(ConductorParameter):
    autostart = True
    priority = -1
    call_in_thread = False
    
    data_filename = '{}.clock_pico'
    nondata_filename = '{}/clock_pico'
    pico_name  = 'clock_pico'
    this_val = None
    last_val = None
    record_sequences = [
    	'all_off_pico',
        #'vrs_horizontal_mot_fluor_cav_perp',
        'gnd',
        'gnd_coherent',
        'gnd_vertical_mot_savePictures_fluor',
        'transport_DDS_ens'
        ]

    def initialize(self, config):
        super(Recorder, self).initialize(config)
        self.connect_to_labrad()
        request = {self.pico_name: {}}
        self.cxn.clock_pico.initialize_devices(json.dumps(request))
        print('Clock pico initialized')
        self.cxn.clock_pico.reset()
        print('Pico reset')


    def get_last_value(self):
        return self.this_val
        
    def get_value(self):
        experiment_name = self.server.experiment.get('name')
        shot_number = self.server.experiment.get('shot_number')
        
        sequence = self.server.parameters.get('sequencer.sequence')
        previous_sequence = self.server.parameters.get('sequencer.previous_sequence')
        value = None
        if (experiment_name is not None) and (sequence is not None):
            point_filename = self.data_filename.format(shot_number)
            rel_point_path = os.path.join(experiment_name, point_filename)
        elif sequence is not None:
            rel_point_path  = self.nondata_filename.format(time.strftime('%Y%m%d'))
        ''' 
        if sequence.loop:
            if np.intersect1d(previous_sequence.value, self.record_sequences):
                value = rel_point_path
        '''
        if np.intersect1d(sequence.value, self.record_sequences):
            value = rel_point_path
        
        #value = self.nondata_filename.format(time.strftime('%Y%m%d'))
        return value
    '''
    @value.setter
    def value(self, x):
        pass
   ''' 
    def update(self):
        val = self.get_value()
        #update last value stored
        self.last_val = self.this_val
        self.this_val = val 
        if val is not None:
            print("Clock pico called with {}".format(val))
            request = {self.pico_name: val}
            self.cxn.clock_pico.record(json.dumps(request))
Parameter = Recorder

