from rf.sg380 import *
from conductor.parameter import ConductorParameter
import time

class Device(SG380):
    _vxi11_address = "192.168.1.18"


class ClockSG380Frequency(ConductorParameter):
    autostart = True
    priority = 3
    dev = None
    last_val = None
    #value = 130870000

    def initialize(self, config):
        super(ClockSG380Frequency, self).initialize(config)
        self.connect_to_labrad()
        self.dev = Device()
        if self.value is not None:
            self.dev.frequency = self.value

    def set_value_lock(self, val):
        if val is not None:
            self.dev.frequency = val
            print('CLOCK SG380 UPDATED IN-CYCLE T0 {} AT {}'.format(val, time.time()))
            self.last_val = val
            
            
    def update(self):
        if self.value is not None:
        	if self.value != self.last_val:
           		self.dev.frequency = self.value
           		#print(self.value)
           		print("SG380Frequency is " + str(self.dev.frequency))
			self.last_val = self.value

Parameter = ClockSG380Frequency
