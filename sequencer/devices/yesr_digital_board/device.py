import json

from device_server.device import DefaultDevice

from sequencer.devices.yesr_sequencer_board.device import YeSrSequencerBoard
from sequencer.devices.yesr_sequencer_board.helpers import time_to_ticks
from sequencer.devices.yesr_digital_board.helpers import get_output

T_TRIGGER = 2e-3
MAX_TICKS = 2**32 - 2**8 # last 8 bits reserverd for specifying external trigger

class YeSrDigitalBoard(YeSrSequencerBoard):
    sequencer_type = 'digital'

    #ok_bitfilename = 'digital_sequencer-v3.1.bit'
    ok_bitfilename = 'digital_sequencer-v3.2.bit'

    channel_mode_wires = [0x01, 0x03, 0x05, 0x07]
    manual_invert_wires = [0x02, 0x04, 0x06, 0x08]
    clk = 50e6 # [Hz]
    
    def update_channel_modes(self):
        cm_list = [c.mode for c in self.channels]
        values = [sum([2**j for j, m in enumerate(cm_list[i:i+16]) 
                if m == 'manual']) for i in range(0, 64, 16)]
        for value, wire in zip(values, self.channel_mode_wires):
            self.fp.SetWireInValue(wire, value)
        self.fp.UpdateWireIns()
        self.update_channel_manual_outputs()
   
    def update_channel_manual_outputs(self): 
        cm_list = [c.mode for c in self.channels]
        cs_list = [c.manual_output for c in self.channels]
        ci_list = [c.invert for c in self.channels]
        values = [sum([2**j for j, (m, s, i) in enumerate(zip(
                cm_list[i:i+16], cs_list[i:i+16], ci_list[i:i+16]))
                if (m=='manual' and s!=i) or (m=='auto' and i==True)]) 
                for i in range(0, 64, 16)]
        for value, wire in zip(values, self.manual_invert_wires):
            self.fp.SetWireInValue(wire, value)
        self.fp.UpdateWireIns()
    
    def default_sequence_segment(self, channel, dt):
        return {'dt': dt, 'out': channel.manual_output}

    def make_sequence_bytes(self, sequence):
        if self.is_master:
            # default trigger to hi
            for s in sequence[self.master_channel]:
                s['out'] = True
    
            # bring trigger channel low for first T_TRIGGER seconds.
            # slaves will start on rising edge of master_channel
            for c in self.channels:
                s = {'dt': T_TRIGGER, 'out': sequence[c.key][0]['out']}
                sequence[c.key].insert(0, s.copy())
                sequence[c.key].append(s.copy())
            sequence[self.master_channel][0]['out'] = False
            sequence[self.master_channel][-1]['out'] = True
    
        # timestamp each state change for each channel sequence by summing over 
        # time intervals
        for c in self.channels:
            total_ticks = 0
            for s in sequence[c.key]:
                dt = time_to_ticks(self.clk, s['dt'])
                s.update({'dt': dt, 't': total_ticks})
                if dt > MAX_TICKS:
                    if c.key == self.master_channel:
                        print "trigger mask:", bin(dt)[26:]
                        s.update({'out': False})
                total_ticks += dt
            sequence[c.key].append({'dt': 1, 't': total_ticks, 'out': sequence[c.key][-1]['out']})

        # each sequence point updates all outs for some number of clock ticks
        # since some channels may have different 'dt's, every time any channel 
        # changes state we need to write all channel outs.
        t_ = sorted(list(set([s['t'] for c in self.channels 
                                     for s in sequence[c.key]])))
        dt_ = [t_[i+1] - t_[i] for i in range(len(t_)-1)]

        programmable_sequence = [(dt, [get_output(sequence[c.key], t) 
                for c in self.channels])
                for dt, t in zip(dt_, t_)]

        sequence_bytes = []
        for t, l in programmable_sequence:
            # each point in sequence specifies all 64 logic outs with 64 bit number
            # e.g. all off is 0...0, channel 1 on is 10...0
#            sequence_bytes += list([sum([2**j for j, b in enumerate(l[i:i+8][::-1]) if b]) 
#                for i in range(0, 64, 8)[::-1]])
            sequence_bytes += list([sum([2**j for j, b in enumerate(l[i:i+8]) if b]) 
                for i in range(0, 64, 8)])
            # time to keep these outs is 32 bit number in units of clk ticks
            sequence_bytes += list([int(eval(hex(t)) >> i & 0xff) 
                    for i in range(0, 32, 8)])
        sequence_bytes += [0] * 12
        return [chr(x) for x in sequence_bytes]
