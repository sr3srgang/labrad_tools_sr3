"""
Conductor parameter to set short transports' duration in sec using Moglabs XRF synthesizer
"""

from conductor.parameter import ConductorParameter


class TransportXRFShortDuration(ConductorParameter):
    autostart = True
    priority = 1
    dev = None
    last_val = None

    def initialize(self, config):
        super(TransportXRFShortDuration, self).initialize(config)
        self.connect_to_labrad()
        
        self.update()
    
    def update(self):
        self.last_val = self.value

Parameter = TransportXRFShortDuration