from sequencer.devices.yesr_analog_board.device import YeSrAnalogBoard
from sequencer.devices.yesr_analog_board.channel import YeSrAnalogChannel

class F(YeSrAnalogBoard):
    autostart = True
    
    conductor_servername = 'conductor'
    ok_servername = 'appa_ok'
    ok_interface = '2047000UX3'
    
    is_master = False

    channels = [
        YeSrAnalogChannel(loc=0, name='11/2 freq mod', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=1, name='H lattice int', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=2, name='top lattice int', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=3, name='bottom lattice in', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=4, name='f4', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=5, name='f5', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=6, name='cav probe', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=7, name='Radial cool int', mode='auto', manual_output=0.0),
        ]


Device = F
