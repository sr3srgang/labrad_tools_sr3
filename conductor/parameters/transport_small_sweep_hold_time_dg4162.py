"""
Conductor parameter to set small transport sweep time in sec
It sets the sweep and return times of RIGOL channels for transport up and down.
"""


from conductor.parameter import ConductorParameter
import os
from rf.DG4162 import *

class TransportSmallDG4162SweepHoldTime(ConductorParameter):
    autostart = True
    priority = 3
    dev_up = None
    dev_down = None
    last_val = None

    def initialize(self, config):
        super(TransportSmallDG4162SweepHoldTime, self).initialize(config)
        self.connect_to_labrad()
        
        # The lines below commented out to deligate the device &
        # value initializations and update to 
        # transport_small_sweep_amp_dg4162.py
        
    #     self.param_name = os.path.splitext(os.path.basename(__file__))[0]
    #     self.dev_up = DG4162(_vxi11_address = "192.168.1.43", is_vervose = True); self.chinx_up = 1 # VLATT RIGOL 3 CH1 for transport up
    #     self.dev_down = DG4162(_vxi11_address = "192.168.1.42", is_vervose = True); self.chinx_down = 1 # VLATT RIGOL 2 CH1 for transport down

        self.update()
    
    def update(self):
        self.last_val = self.value
            
    # # def update(self):
    #     if self.value is not None:
    #         # if self.value != self.last_val:
    #         self.dev_up.sweep_hold_time[self.chinx_up] = self.value
    #         self.dev_down.sweep_hold_time[self.chinx_down] = self.value
    #         print(self.param_name + " is " + str(self.value))
    #         self.dev_up.set_local()
    #         self.dev_down.set_local()
    #         self.last_val = self.value
            
        
        

Parameter = TransportSmallDG4162SweepHoldTime