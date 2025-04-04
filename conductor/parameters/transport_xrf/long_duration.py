"""
Conductor parameter to set long transports' duration in sec using Moglabs XRF synthesizer
"""

from conductor.parameter import ConductorParameter


class TransportXRFLongDuration(ConductorParameter):
    autostart = True
    priority = 1
    dev = None
    last_val = None

    def initialize(self, config):
        super(TransportXRFLongDuration, self).initialize(config)
        self.connect_to_labrad()
        
        self.update()
    
    def update(self):
        self.last_val = self.value

Parameter = TransportXRFLongDuration