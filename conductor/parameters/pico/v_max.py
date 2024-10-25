import json
import numpy as np
import os
import time

from twisted.internet.defer import inlineCallbacks

from conductor.parameter import ConductorParameter

class VoltageMax(ConductorParameter):
    autostart = False#True
    priority = -1
    call_in_thread = False
    current_val = None
    
    pico_name  = 'cavity_pico'

    def initialize(self, config):
        super(VoltageMax, self).initialize(config)
        self.connect_to_labrad()
        request = {self.pico_name: {}}
        self.cxn.pico.initialize_devices(json.dumps(request))
        print('Cavity pico initialized')


    def update(self):
        val = self.get_value()
        if val is not None:
        	if self.current_val != val:
            		request = {self.pico_name: val}
            		self.cxn.pico.set_max_V(json.dumps(request))
            		print('Pico max voltage set to {}'.format(val))
            		self.current_val = val
Parameter = VoltageMax

