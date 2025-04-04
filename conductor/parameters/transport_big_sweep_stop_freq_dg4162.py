from conductor.parameter import ConductorParameter
import os
from rf.DG4162 import *
from influxdb.influxdb_write_py27 import *


class TransportBigDG4162SweepStopFrequency(ConductorParameter):
    autostart = True
    priority = 3
    dev = None
    last_val = None

    def initialize(self, config):
        super(TransportBigDG4162SweepStopFrequency, self).initialize(config)
        self.connect_to_labrad()
        self.param_name = os.path.splitext(os.path.basename(__file__))[0]
        self.dev =  DG4162(_vxi11_address = "192.168.1.41", is_vervose = False); self.chinx = 1 # VLATT RIGOL 1 CH1 for transport up
        
        self.update()

            
    def update(self):
        if self.value is not None:
            # if self.value != self.last_val:
            self.dev.sweep_stop_frequency[self.chinx] = self.value
            # print(self.param_name + " is " + str(self.dev.sweep_stop_frequency[self.chinx]))
            self.last_val = self.value
            
        self.upload_influxdb()
            
    
    def upload_influxdb(self):
        """Upload relevant values to InfluxDB"""
        write_influxdb('transport_big_sweep_stop_freq_dg4162', self.dev.sweep_stop_frequency[self.chinx])

Parameter = TransportBigDG4162SweepStopFrequency