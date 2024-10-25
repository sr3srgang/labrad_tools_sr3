from current_controller.devices.ldc50 import LDC50, LDC50Proxy

class Device(LDC50):
    _socket_address = ('192.168.1.12', 8888)
    _current_range = (0.0, 0.400)
    _relock_stepsize = 0.001
    _locked_threshold = 160e-3


class DeviceProxy(Device, LDC50Proxy):
    _socket_servername = 'appa_socket'

    def __init__(self, cxn=None, **kwargs):
        LDC50Proxy.__init__(self, cxn, **kwargs)

dev = Device()
print(dev.power)

