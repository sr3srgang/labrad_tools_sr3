import json
import time
import os
import traceback

from twisted.internet.defer import inlineCallbacks

from conductor.parameter import ConductorParameter

class Plot(ConductorParameter):
    autostart = False
    data_directory = "/home/srgang/K/data/data"
    priority = 1

    
    def initialize(self,config):
        self.connect_to_labrad()
    
    def update(self):
        experiment_name = self.server.experiment.get('name')
        print(experiment_name)
        if self.value and (experiment_name is not None):
	    try:
                settings = json.loads(self.value)
                settings['data_path'] = self.data_directory
                settings['shot_number'] = self.server.experiment.get('shot_number')
                settings['exp_name'] = experiment_name
            	self.cxn.plotter.plot(json.dumps(settings))
            except:
                traceback.print_exc()

Parameter = Plot
