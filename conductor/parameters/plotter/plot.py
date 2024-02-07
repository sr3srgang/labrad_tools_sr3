import json
import time
import os
import traceback

from twisted.internet.defer import inlineCallbacks

from conductor.parameter import ConductorParameter

class Plot(ConductorParameter):
    autostart = False
    data_directory = "/K/data/data"
    priority = 1

    
    def initialize(self,config):
        self.connect_to_labrad()
    
    def update(self):
        experiment_name = self.server.experiment.get('name')
        if self.value and (experiment_name is not None):
	    try:
                settings = json.loads(self.value)
                experiment_directory = os.path.join(self.data_directory,experiment_name)
                settings['data_path'] = experiment_directory
            	self.cxn.plotter.plot(json.dumps(settings))
            except:
                traceback.print_exc()

Parameter = Plot
