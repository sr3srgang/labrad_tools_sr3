"""
Conductor parameter to set small transports' distance using Moglabs XRF synthesizer
"""

from conductor.parameter import ConductorParameter


class TransportXRFSmallDistance(ConductorParameter):
    autostart = True
    priority = 1
    dev = None
    last_val = None

    def initialize(self, config):
        super(TransportXRFSmallDistance, self).initialize(config)
        self.connect_to_labrad()
        
        self.update()
    
    def update(self):
        self.last_val = self.value

Parameter = TransportXRFSmallDistance