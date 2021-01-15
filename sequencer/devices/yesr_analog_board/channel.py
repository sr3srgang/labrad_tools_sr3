import json

from sequencer.devices.yesr_analog_board.ramps import RampMaker

class YeSrAnalogChannel(object):
    channel_type = 'analog'
    dac_voltage_range = (-10.0, 10.0)
    dac_bits = 16
    sequence = None
    programmable_sequence = None

    def __init__(self, loc=None, name=None, mode='auto', manual_output=0.0, 
            voltage_range=(-10.0, 10.0), alt_keys=[]):
        self.loc = int(loc)
        self.name = str(name)
        self.mode = str(mode)
        self.manual_output = float(manual_output)
        self.software_voltage_range = voltage_range
        self.min_voltage = min(voltage_range)
        self.max_voltage = max(voltage_range)
        self.alt_keys = alt_keys

    def set_board(self, board):
        self.board = board
        self.board_name = board.name
        self.board_loc = board.name.upper() + str(self.loc).zfill(2)
        self.key = self.name + '@' + self.board_loc
    
    def set_sequence(self, sequence):
        self.sequence = sequence
        self.programmable_sequence = RampMaker(sequence).get_programmable()
    
    def get_info(self):
        info = {x: getattr(self, x) for x in dir(self) if x[0] != '_'}
        info = json.loads(json.dumps(info, default=lambda x: None))
        info = {k: v for k, v in info.items() if v is not None}
        if 'sequence' in info:
            info.pop('sequence')
        if 'programmable_sequence' in info:
            info.pop('programmable_sequence')
        return info

    def set_mode(self, mode):
        if mode not in ('auto', 'manual'):
            message = 'channel mode {} not valid'.format(mode)
            raise Exception(message)
        self.mode = mode

    def get_mode(self):
        return self.mode
    
    def set_manual_output(self, manual_output):
        if not (self.min_voltage <= manual_output <= self.max_voltage):
            message = 'channel output {} not in range [{}, {}]'.format(mode, 
                self.min_voltage, self.max_voltage)
            raise Exception(message)
        self.manual_output = manual_output

    def get_manual_output(self):
        return self.manual_output
