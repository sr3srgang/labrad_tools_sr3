import rf.devices.ad9956.device
reload(rf.devices.ad9956.device)
from rf.devices.ad9956.device import AD9956

class Channel(AD9956):
    autostart = True
    serial_servername = "appa_serial"
    serial_address = "/dev/ttyACM85332343432351F0E180"
    board_num = 1
    channel = 0

    default_frequency = 57.622e6 #Default clock aom frequency

Device = Channel
