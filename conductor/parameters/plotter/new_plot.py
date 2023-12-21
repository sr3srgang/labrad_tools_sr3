import json
from copy import deepcopy
import traceback

from labrad.wrappers import connectAsync
from twisted.internet.defer import inlineCallbacks

from matplotlib import pyplot as plt

from conductor.parameter import ConductorParameter

class NewPlot(ConductorParameter):
    priority = 1

    autostart = False
    def initialize(self,config):
        self.connect_to_labrad()
    
    def update(self):
        try:
            data_copy = self.server._get_parameter_values("{}",True)
            if self.value:
                self.cxn.new_plotter.plot(json.dumps(self.value), 
                        json.dumps(data_copy, default=lambda x: None))
        except:
            traceback.print_exc()

Parameter = NewPlot
