"""
Conductor parameter to set frequency gain of 16ns-rate control (XPARAM) of Moglabs XRF synthesizer
"""

from conductor.parameter import ConductorParameter


class TransportXRFFreqGain(ConductorParameter):
    autostart = True
    priority = 1
    dev = None
    last_val = None

    def initialize(self, config):
        super(TransportXRFFreqGain, self).initialize(config)
        self.connect_to_labrad()
        
        self.update()
    
    def update(self):
        self.last_val = self.value

Parameter = TransportXRFFreqGain