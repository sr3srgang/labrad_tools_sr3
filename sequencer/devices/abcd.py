from sequencer.devices.yesr_digital_board.device import YeSrDigitalBoard
from sequencer.devices.yesr_digital_board.channel import YeSrDigitalChannel

class ABCD(YeSrDigitalBoard):
    autostart = True
    conductor_servername = 'conductor'
    ok_servername = 'appa_ok'
    ok_interface = '2047000UVN'#Y2'#VN'

    is_master = True
    channels = [
        YeSrDigitalChannel(loc=['A', 0], name='Zeeman Shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 1], name='2D MOT Shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 2], name='2D MOT AOM', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 3], name='3D MOT Shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 4], name='Free/nothing', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 5], name='3D MOT on/off', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 6], name='Imaging Laser Shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 7], name='Imaging AOM', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 8], name='H MOT camera', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 9], name='11/2 FM', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 10], name='11/2 Shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 11], name='11/2 MOT AOM', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 12], name='V MOT camera', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 13], name='Transport trigger', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 14], name='Mystery camera', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 15], name='Repump AOM', mode='auto', manual_output=False, invert=False),
        
        YeSrDigitalChannel(loc=['B', 0], name='Clock shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 1], name='Second clock AOM (switch)', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 2], name='B2', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 3], name='Clock synth switch', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 4], name='Optical pumping shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 5], name='Repump shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 6], name='Pico trigger', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 7], name='S/H clock intensity', mode='auto', manual_output=False, invert=True),
        YeSrDigitalChannel(loc=['B', 8], name='Pi/0.5*pi', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 9], name='BROKEN', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 10], name='Pi pulse trigger', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 11], name='Pi/2 pulse trigger', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 12], name='rad cool aom', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 13], name='11/2 freq mod switch', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 14], name='B14', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 15], name='S/H lat. phase', mode='auto', manual_output=False, invert=True),
        
        YeSrDigitalChannel(loc=['C', 0], name='C0', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 1], name='C1', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 2], name='C2', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 3], name='C3', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 4], name='C4', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 5], name='C5', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 6], name='C6', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 7], name='C7', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 8], name='C8', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 9], name='C9', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 10], name='C10', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 11], name='C11', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 12], name='C12', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 13], name='C13', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 14], name='C14', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 15], name='C15', mode='auto', manual_output=False, invert=False),
        
        YeSrDigitalChannel(loc=['D', 0], name='Cavity AOM shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 1], name='Cavity AOM sweep', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 2], name='Other mystery camera', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 3], name='Something cavity optics?', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 4], name='Optical pumping AOM', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 5], name='Cavity pico trigger', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 6], name='Clock readout EOM sweep', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 7], name='QND EOM sweep', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 8], name='D8', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 9], name='D9', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 10], name='D10', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 11], name='D11', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 12], name='D12', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 13], name='D13', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 14], name='D14', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 15], name='Trigger', mode='auto', manual_output=False, invert=False),
        ]
    
        
Device = ABCD
