from rf.sg380 import *
from conductor.parameter import ConductorParameter

class Device(SG380):
    _vxi11_address = "192.168.1.17"


class ClockPulseSG380Frequency(ConductorParameter):
    autostart = True
    priority = 3
    dev = None
    last_val = None
    #value = 130870000

    def initialize(self, config):
        super(ClockPulseSG380Frequency, self).initialize(config)
        self.connect_to_labrad()
        self.dev = Device()
        if self.value is not None:
            self.dev.frequency = self.value

    def update(self):
        if self.value is not None:
        	if self.value != self.last_val:
           		self.dev.frequency = self.value
           		#print(self.value)
           		print("SG380 (Pulse) Frequency is " + str(self.dev.frequency))
			self.last_val = self.value

Parameter = ClockPulseSG380Frequency