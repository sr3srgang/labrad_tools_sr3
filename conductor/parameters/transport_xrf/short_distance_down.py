"""
Conductor parameter to set short transports' distance using Moglabs XRF synthesizer
"""

from conductor.parameter import ConductorParameter


class TransportXRFShortDistance(ConductorParameter):
    autostart = True
    priority = 1
    dev = None
    last_val = None

    def initialize(self, config):
        super(TransportXRFShortDistance, self).initialize(config)
        self.connect_to_labrad()
        
        self.update()
    
    def update(self):
        self.last_val = self.value

Parameter = TransportXRFShortDistance