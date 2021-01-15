import json
import time

from conductor.parameter import ConductorParameter

class PreviousSequence(ConductorParameter):
    autostart = True
    priority = 11
    value_type = 'list'
    value = None

    sequencer_servername = 'sequencer'
    master_device = 'abcd'
    
    def initialize(self, config):
        super(PreviousSequence, self).initialize(config)
        self.connect_to_labrad()
        self.sequencer_server = getattr(self.cxn, self.sequencer_servername)
    
    def update(self):
        request = {self.master_device: None}
        response = json.loads(self.sequencer_server.sequence(json.dumps(request)))
        self.value = response[self.master_device]

Parameter = PreviousSequence
