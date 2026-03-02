import json
import os
import time
from data_analysis.cavity_clock.read_data import *
from data_analysis.cavity_clock.helpers import *
from twisted.internet import reactor
from conductor.parameter import ConductorParameter
from data_analysis.PID import PID

# the value of this parameter (PmtLock.vallue) should be a dict with PID p 

class SweepBzRed(ConductorParameter):
    autostart = True
    priority = 10
    data_directory = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    #data_filename = '{}.conductor.json'
    call_in_thread = False
    sweep_up = .2
    sweep_down = .2

    def initialize(self, config):
    	print('TESTING')
        super(SweepBzRed, self).initialize(config)
        self.connect_to_labrad()
        c_up = config.get('sweep_up')
        c_down = config.get('sweep_down')
        if c_up is not None:
            self.sweep_up = c_up
        if c_down is not None:
            self.sweep_down = c_down
        print('TEST CONFIRMED')
        
        
    def update(self):
    	    BzRedVal = self.server.parameters.get('sequencer.BzRed').get_value()
    	    self.server.parameters.get('sequencer.BzRedH').set_value(BzRedVal + self.sweep_up)
    	    self.server.parameters.get('sequencer.BzRedL').set_value(BzRedVal - self.sweep_down)
    	    print('updated BzRed sweeps')
        
    
Parameter = SweepBzRed
