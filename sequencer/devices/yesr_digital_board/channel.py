import json

class YeSrDigitalChannel(object):
    channel_type = 'digital'
    sequence = None
    programmable_sequence = None

    def __init__(self, loc=None, name=None, mode='auto', manual_output=False,
            invert=False):
        self.loc = loc
        self.name = str(name)
        self.mode = str(mode)
        self.manual_output = bool(manual_output)
        self.invert = bool(invert)
        self.alt_keys = []

    def set_board(self, board):
        self.board = board
        self.board_name = board.name
        row, column = self.loc
        self.board_loc = str(row) + str(column).zfill(2)
        self.key = self.name + '@' + self.board_loc
    
    def set_sequence(self, sequence):
        self.sequence = sequence
    
    def get_info(self):
        info = {x: getattr(self, x) for x in dir(self) if x[0] != '_'}
        info = json.loads(json.dumps(info, default=lambda x: None))
        info = {k: v for k, v in info.items() if v is not None}
        return info
    
    def set_mode(self, mode):
        if mode not in ('auto', 'manual'):
            message = 'channel mode ({}) not valid'.format(mode)
            raise Exception(message)
        self.mode = mode

    def get_mode(self):
        return self.mode

    def set_manual_output(self, state):
        self.manual_output = bool(state)

    def get_manual_output(self):
        return bool(self.manual_output)
    
