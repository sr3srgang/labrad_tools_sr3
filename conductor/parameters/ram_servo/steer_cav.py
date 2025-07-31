import json
import os
import time
from data_analysis.cavity_clock.read_data import *
from data_analysis.cavity_clock.helpers import *
from twisted.internet import reactor
from conductor.parameter import ConductorParameter
from data_analysis.PID import PID



class RamServoLock(ConductorParameter):
    autostart = False
    priority = 10
    data_directory = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    #data_filename = '{}.conductor.json'
    call_in_thread = False
    default = 102.160e6

    def initialize(self, config):
        super(RamServoLock, self).initialize(config)
        self.connect_to_labrad()
        
        print("config:")
        print(config)
        active = config.get('servo_active')
        self.active = active
        if active:
		default_val = config.get('script_default')
		if default_val is not None:
		    self.default = default_val
		#TUNE THESE!!
		self.PID_params = {"k_prop": -1, "t_int": 10, "t_diff": 0, "setpoint":.5,  "dt": 1, "output_default":self.default}
		self.PID = PID(self.PID_params)
		print('Turning on cav ram servo')
        
    def update(self):
    	if self.active:
		print('ram servo update at {}'.format(time.time()))
		
		err_sig = self.server.parameters.get('bare_dac_voltage').value
		if err_sig is not None:
		    out = self.PID.update(err_sig)
		    print("new cav aom val from ram servo: {}".format(out))
		    self.server.parameters.get('cav_aom_813_rigol').set_value_lock(out)
		    
        
        
        
        
    
Parameter = RamServoLock
