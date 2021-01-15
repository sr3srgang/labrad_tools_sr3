from sequencer.devices.yesr_analog_board.device import YeSrAnalogBoard
from sequencer.devices.yesr_analog_board.channel import YeSrAnalogChannel

class E(YeSrAnalogBoard):
    autostart = True
    
    conductor_servername = 'conductor'
    ok_servername = 'appa_ok'
    ok_interface = '1401000AT3'
    
    is_master = False

    channels = [
        YeSrAnalogChannel(loc=0, name='Alpha Intensity', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=1, name='Beta Intensity', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=2, name='X Comp. Coil', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=3, name='Y Comp. Coil', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=4, name='Z Comp. Coil', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=5, name='MOT Coil', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=6, name='HODT Intensity', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=7, name='VODT Intensity', mode='auto', manual_output=0.0),
        ]


Device = E
