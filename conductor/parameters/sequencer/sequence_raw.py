import json

from twisted.internet.defer import inlineCallbacks

from conductor.parameter import ConductorParameter

class SequenceRaw(ConductorParameter):
    autostart = False
    priority = 9
    value_type = 'data'

    @inlineCallbacks
    def initialize(self):
        yield self.connect()
        self.sequencer_server = getattr(self.cxn, self.sequencer_servername)
        yield self.update()
    
    @inlineCallbacks
    def update(self):
        """ value is dict of channel sequences """
        sequence_raw_json = yield self.sequencer_server.get_sequence()
        self.value = json.loads(sequence_raw_json)

Parameter = SequenceRaw
