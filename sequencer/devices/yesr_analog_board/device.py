import json

from device_server.device import DefaultDevice

from sequencer.devices.yesr_sequencer_board.device import YeSrSequencerBoard
from sequencer.devices.yesr_analog_board.ramps import RampMaker
from sequencer.devices.yesr_analog_board.helpers import seconds_to_ticks
from sequencer.devices.yesr_analog_board.helpers import volts_to_bits
from sequencer.devices.yesr_analog_board.helpers import get_ramp_bytes

# max timestep for digital sequencer
# (2**32 - 2**8) / (50 MHz)
T_TRIGGER = 85.8993408 # [s]

class YeSrAnalogBoard(YeSrSequencerBoard):
    sequencer_type = 'analog'

    #ok_bitfilename = 'analog_sequencer-v3.1.2.bit'
    ok_bitfilename = 'analog_sequencer-v3.2.bit'
    
    channel_mode_wire = 0x09
    manual_voltage_wires = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08]
    clk = 50e6 / (2 * 8) # [Hz]
    
    def update_channel_modes(self):
        cm_list = [c.mode for c in self.channels]
        value = sum([2**j for j, m in enumerate(cm_list) if m == 'manual'])
        value = 0b0000000000000000 | value
        self.fp.SetWireInValue(self.channel_mode_wire, value)
        self.fp.UpdateWireIns()
    
    def update_channel_manual_outputs(self): 
        for c, w in zip(self.channels, self.manual_voltage_wires):
            v = volts_to_bits(c.manual_output - min(c.dac_voltage_range), c.dac_voltage_range, c.dac_bits)
            self.fp.SetWireInValue(w, v)
        self.fp.UpdateWireIns()
    
    def default_sequence_segment(self, channel, dt):
        return {'dt': dt, 'type': 's', 'vf': channel.manual_output}

    def make_sequence_bytes(self, sequence):
        for channel in self.channels:
            sequence[channel.key] = [s for s in sequence[channel.key] if s['dt'] < T_TRIGGER]
            channel_sequence = sequence[channel.key]
            channel.set_sequence(channel_sequence)
        
        unsorted_ramps = []
        channel_stop_ticks = {}
        for channel in self.channels:
            for ramp in channel.programmable_sequence:
                vi_bits = volts_to_bits(ramp['vi'], channel.dac_voltage_range, channel.dac_bits)
                vf_bits = volts_to_bits(ramp['vf'], channel.dac_voltage_range, channel.dac_bits)
                dv_bits = vf_bits - vi_bits

                ti_ticks = seconds_to_ticks(ramp['ti'], self.clk)
                tf_ticks = seconds_to_ticks(ramp['tf'], self.clk)
                dt_ticks = tf_ticks - ti_ticks

                ramp_bytes = get_ramp_bytes(dv_bits, dt_ticks)

                unsorted_ramps.append((ti_ticks, channel.loc, ramp_bytes))
            channel_stop_ticks.update({channel.loc: tf_ticks})

        device_stop_ticks = max(channel_stop_ticks.values())
        for channel in self.channels:
            if channel_stop_ticks[channel.loc] < device_stop_ticks:
                ti_ticks = channel_stop_ticks[channel.loc]
                dt_ticks = device_stop_ticks - ti_ticks
                dv_bits = 0
                ramp_bytes = get_ramp_bytes(dv_bits, dt_ticks)
                unsorted_ramps.append((ti_ticks, channel.loc, ramp_bytes))
        
        sorted_ramps = sorted(unsorted_ramps)

        sequence_bytes = []
        for (t, loc, ramp_bytes) in sorted_ramps:
            sequence_bytes += ramp_bytes
        sequence_bytes += [0] * 6
        return [chr(x) for x in sequence_bytes]
