"""
Conductor parameter to set long transports' distance using Moglabs XRF synthesizer
"""

from conductor.parameter import ConductorParameter


class TransportXRFLongDistance(ConductorParameter):
    autostart = True
    priority = 1
    dev = None
    last_val = None

    def initialize(self, config):
        super(TransportXRFLongDistance, self).initialize(config)
        self.connect_to_labrad()
        
        self.update()
    
    def update(self):
        self.last_val = self.value

Parameter = TransportXRFLongDistance