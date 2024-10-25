import json
import time
import os
import traceback

from twisted.internet.defer import inlineCallbacks

from conductor.parameter import ConductorParameter

class Plot(ConductorParameter):
    autostart = False
<<<<<<< HEAD
    data_directory = "/home/srgang/K/data/data"
=======
    data_directory = "/K/data/data"
>>>>>>> fe00ddafa6ddde9495657f9d0419a8b27b310496
    priority = 1

    
    def initialize(self,config):
        self.connect_to_labrad()
    
    def update(self):
        experiment_name = self.server.experiment.get('name')
<<<<<<< HEAD
        print(experiment_name)
        if self.value and (experiment_name is not None):
	    try:
                settings = json.loads(self.value)
                settings['data_path'] = self.data_directory
                settings['shot_number'] = self.server.experiment.get('shot_number')
                settings['exp_name'] = experiment_name
=======
        if self.value and (experiment_name is not None):
	    try:
                settings = json.loads(self.value)
                experiment_directory = os.path.join(self.data_directory,experiment_name)
                settings['data_path'] = experiment_directory
>>>>>>> fe00ddafa6ddde9495657f9d0419a8b27b310496
            	self.cxn.plotter.plot(json.dumps(settings))
            except:
                traceback.print_exc()

Parameter = Plot
