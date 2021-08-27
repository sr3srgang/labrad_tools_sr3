from sequencer.devices.yesr_analog_board.device import YeSrAnalogBoard
from sequencer.devices.yesr_analog_board.channel import YeSrAnalogChannel

class E(YeSrAnalogBoard):
    autostart = True
    
    conductor_servername = 'conductor'
    ok_servername = 'appa_ok'
    ok_interface = '1401000AT3'
    
    is_master = False

    channels = [
        YeSrAnalogChannel(loc=0, name='Clock phase', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=1, name='Clock int ext cont', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=2, name='Bias X', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=3, name='Bias Y', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=4, name='Bias Z', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=5, name='MOT Coil', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=6, name='11/2 Intensity', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=7, name='9/2 Intensity', mode='auto', manual_output=0.0),
        ]


Device = E
