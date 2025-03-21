"""
Conductor parameter to set small transports' duration in sec using Moglabs XRF synthesizer
"""

from conductor.parameter import ConductorParameter


class TransportXRFSmallDuration(ConductorParameter):
    autostart = True
    priority = 1
    dev = None
    last_val = None

    def initialize(self, config):
        super(TransportXRFSmallDuration, self).initialize(config)
        self.connect_to_labrad()
        
        self.update()
    
    def update(self):
        self.last_val = self.value

Parameter = TransportXRFSmallDuration