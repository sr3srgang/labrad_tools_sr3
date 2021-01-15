from conductor.parameter import ConductorParameter

class Parameter(ConductorParameter):
    autostart = False
    call_in_thread = False

    def initialize(self, config):
	print 'fake clock aom initializing'
        print 'hello, world!'
        
    def update(self):
        print 'hi hello'

