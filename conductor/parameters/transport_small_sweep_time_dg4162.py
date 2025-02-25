"""
Conductor parameter to set small transport sweep time in sec
It sets the sweep and return times of RIGOL channels for transport up and down.
"""


from conductor.parameter import ConductorParameter
import os
from rf.DG4162 import *
from influxdb.influxdb_write import *

class TransportSmallDG4162SweepTime(ConductorParameter):
    autostart = False
    priority = 3
    dev_up = None
    dev_down = None
    last_val = None
    

    def initialize(self, config):
        super(TransportSmallDG4162SweepTime, self).initialize(config)
        self.connect_to_labrad()
        self.param_name = os.path.splitext(os.path.basename(__file__))[0]
        self.dev_up = DG4162(_vxi11_address = "192.168.1.43", is_vervose = False); self.chinx_up = 1 # VLATT RIGOL 3 CH1 for transport up
        self.dev_down = DG4162(_vxi11_address = "192.168.1.42", is_vervose = False); self.chinx_down = 1 # VLATT RIGOL 2 CH1 for transport down
        
        self.update()


    def update(self):
        if self.value is not None:
            # if self.value != self.last_val:
            self.dev_up.sweep_time[self.chinx_up] = self.value
            self.dev_down.sweep_time[self.chinx_down] = self.value
            print(self.param_name + " is " + str(self.value))
            self.dev_up.set_local()
            self.dev_down.set_local()
            self.last_val = self.value
            
            self.upload_influxdb()


    def upload_influxdb(self):
        """Upload relevant values to InfluxDB"""
        fields = {
            self.param_name: self.value,
        }
        
        write_influxdb_fields(fields)
        
        

Parameter = TransportSmallDG4162SweepTime