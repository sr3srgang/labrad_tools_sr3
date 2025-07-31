from rf.DG4162 import *
from conductor.parameter import ConductorParameter
import time

class Device(DG4162):
    _vxi11_address = "192.168.1.23" #idk


class aomDG4162Frequency(ConductorParameter):
    autostart = True
    priority = 3 #idk
    dev = None
    last_val = None
    

    def initialize(self, config):
        super(aomDG4162Frequency, self).initialize(config)
        self.connect_to_labrad()
        self.dev = Device()
        if self.value is not None:
            self.dev.frequency = self.value

    def set_value_lock(self, val):
        if val is not None:
            print('WOULD SET RIGOL VAL BUT CURRENTLY TESTING')
            #self.value = val
            
            
            
    def update(self):
        if self.value is not None:
        	if self.value != self.last_val:
           		#self.dev.frequency = self.value
           		self.dev.set_channel_freq(1, self.value)
           		#print(self.value)
           		#print("DG4162Frequency is " + str(self.dev.frequency))
			self.last_val = self.value

Parameter = aomDG4162Frequency
