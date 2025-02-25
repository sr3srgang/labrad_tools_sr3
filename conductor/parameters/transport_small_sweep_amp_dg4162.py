"""
Conductor parameter to set small transport sweep frequency "amplitude" in Hz.
It sets the sweep stop frequencies of RIGOL channels for transport up and down,
antisymmetically by the same magnitude, from the given carrier frequencies
(in `sweep_start_frequency_up` & `sweep_start_frequency_down` variables).
"""

from conductor.parameter import ConductorParameter
import os
from rf.DG4162 import *
from influxdb.influxdb_write import *

class TransportSmallDG4162SweepAmplitude(ConductorParameter):
    autostart = False
    priority = 3
    dev_up = None
    dev_down = None
    last_val = None
    sweep_start_frequency_up = 31e6
    sweep_start_frequency_down = 19e6

    def initialize(self, config):
        super(TransportSmallDG4162SweepAmplitude, self).initialize(config)
        self.connect_to_labrad()
        self.param_name = os.path.splitext(os.path.basename(__file__))[0]
        self.dev_up = DG4162(_vxi11_address = "192.168.1.43", is_vervose = False); self.chinx_up = 1 # VLATT RIGOL 3 CH1 for transport up
        self.dev_down = DG4162(_vxi11_address = "192.168.1.42", is_vervose = False); self.chinx_down = 1 # VLATT RIGOL 2 CH1 for transport down
        
        self.update()
            
            
    def update(self):
        if self.value is not None:
            # if self.value != self.last_val:
            self.dev_up.sweep_stop_frequency[self.chinx_up] = self.sweep_start_frequency_up + self.value
            self.dev_down.sweep_stop_frequency[self.chinx_down] = self.sweep_start_frequency_down - self.value
            print(self.param_name + " is " + str(self.value))
            self.dev_up.set_local()
            self.dev_down.set_local()
            self.last_val = self.value
            
            self.upload_influxdb()
            
    def upload_influxdb(self):
        """Upload relevant values to InfluxDB"""
        fields = {
            self.param_name: self.value,
            'transport_small_up_sweep_start_freq_dg4162': self.dev_up.sweep_start_frequency[self.chinx_up],
            'transport_small_up_sweep_stop_freq_dg4162': self.dev_up.sweep_stop_frequency[self.chinx_up],
        }
        
        write_influxdb_fields(fields)
        
        

Parameter = TransportSmallDG4162SweepAmplitude