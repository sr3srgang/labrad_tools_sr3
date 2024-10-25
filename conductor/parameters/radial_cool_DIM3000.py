from rf.DIM3000 import *
from conductor.parameter import ConductorParameter
import time

class Device(DIM3000):
    _telnetlib_host = "192.168.1.100"
    _telnetlib_port = "8081"
    _custom_name = "SN2210"


class RadialCoolDIM3000Frequency(ConductorParameter):
    autostart = True
    priority = 4
    dev = None
    last_val = None
    #value = 130870000

    def initialize(self, config):
        super(RadialCoolDIM3000Frequency, self).initialize(config)
        self.connect_to_labrad()
        self.dev = Device()
        if self.value is not None: # ?? what does this clause do?
            self.dev.frequency = self.value

    def set_value_lock(self, val):
        if val is not None:
            self.dev.frequency = val
            print('RADIAL COOL DIM3000 UPDATED IN-CYCLE T0 {} AT {}'.format(val, time.time()))
            self.last_val = val
            
            
    def update(self):
        if self.value is not None:
            if self.value != self.last_val:
                self.dev.frequency = self.value
                #print(self.value)
                # querying does not work for now... just copying the set freq
                # print("RadialCoolDIM3000Frequency is " + str(self.dev.frequency))
                print("RadialCoolDIM3000Frequency is " + str(self.value))
            self.last_val = self.value

Parameter = RadialCoolDIM3000Frequency
