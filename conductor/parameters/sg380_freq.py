from rf.sg380 import *
from conductor.parameter import ConductorParameter

class Device(SG380):
    _vxi11_address = "192.168.1.10"


class SG380Frequency(ConductorParameter):
    autostart = True
    priority = 3
    dev = None
    #value = 130870000

    def initialize(self, config):
        super(SG380Frequency, self).initialize(config)
        self.connect_to_labrad()
        self.dev = Device()
        if self.value is not None:
            self.dev.frequency = self.value

    def update(self):
        if self.value is not None:
           self.dev.frequency = self.value
        #print(self.value)
        #print("SG380Frequency is " + str(self.dev.frequency))


Parameter = SG380Frequency
