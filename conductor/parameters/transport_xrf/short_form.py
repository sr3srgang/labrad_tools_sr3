"""
Conductor parameter to set short transports' trajectory form using Moglabs XRF synthesizer
"""

from conductor.parameter import ConductorParameter


class TransportXRFShortTransportForm(ConductorParameter):
    autostart = True
    priority = 1
    dev = None
    last_val = None

    def initialize(self, config):
        super(TransportXRFShortTransportForm, self).initialize(config)
        self.connect_to_labrad()
        
        self.update()
    
    def update(self):
        self.last_val = self.value

Parameter = TransportXRFShortTransportForm