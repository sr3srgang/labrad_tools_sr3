"""
Conductor parameter to set long if the transport is to be legacy one.
"""

from conductor.parameter import ConductorParameter

class TransportXRFUpdateShot(ConductorParameter):
    autostart = True
    priority = 1
    dev = None
    last_val = None

    def initialize(self, config):
        super(TransportXRFUpdateShot, self).initialize(config)
        self.connect_to_labrad()
        
        self.update()
    
    def update(self):
        self.last_val = self.value

Parameter = TransportXRFUpdateShot