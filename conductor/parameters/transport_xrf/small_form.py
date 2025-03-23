"""
Conductor parameter to set small transports' trajectory form using Moglabs XRF synthesizer
"""

from conductor.parameter import ConductorParameter


class TransportXRFSmallTransportForm(ConductorParameter):
    autostart = True
    priority = 1
    dev = None
    last_val = None

    def initialize(self, config):
        super(TransportXRFSmallTransportForm, self).initialize(config)
        self.connect_to_labrad()
        
        self.update()
    
    def update(self):
        self.last_val = self.value

Parameter = TransportXRFSmallTransportForm