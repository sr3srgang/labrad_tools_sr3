import rf.devices.ad9956.device
reload(rf.devices.ad9956.device)
from rf.devices.ad9956.device import AD9956

class Channel(AD9956):
    autostart = True
    serial_servername = "appa_serial"
    serial_address = "/dev/ttyACM0" #"/dev/ttyACM85332343432351F0E180"
    board_num = 0
    channel = 0

    default_frequency = 110e6 #135.374e6 #Default fiber noise frequency

Device = Channel
