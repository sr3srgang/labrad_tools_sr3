import json
import os
import time
from data_analysis.cavity_clock.read_data import *
from data_analysis.cavity_clock.helpers import *
from twisted.internet import reactor
from conductor.parameter import ConductorParameter
from data_analysis.PID import PID

# the value of this parameter (PmtLock.vallue) should be a dict with PID p 

class PmtLockChop(ConductorParameter):
    autostart = False
    priority = 10
    data_directory = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    #data_filename = '{}.conductor.json'
    call_in_thread = False
    default = 885387.35 + 116.55e6
    errorSig = 0

    def initialize(self, config):
        super(PmtLockChop, self).initialize(config)
        self.connect_to_labrad()
        
        print("config:")
        print(config)
        active = config.get('servo_active')
        self.active = active
        if active:
		default_val = config.get('script_default')
		if default_val is not None:
		    self.default = default_val
		# self.PID_params = {"k_prop": -1, "t_int": 10, "t_diff": 0, "setpoint":0,  "dt": 1, "output_default":self.default}
		self.PID_params = {"k_prop": -1, "t_int": 10, "t_diff": 0, "setpoint":0,  "dt": 1, "output_default":self.default}
		self.PID = PID(self.PID_params)
		self.server.parameters.get('clock_sg380').set_value_lock(self.default)
		print('Running a pmt clock lock')
        
    def update(self):
    	if self.active:
    		
		print('Lock update at {}'.format(time.time()))
		#Data file to use:
		df = self.server.parameters.get('pico.clock_recorder').get_last_value() #want to find the data file from last shot during this blue mot loading
		if df is not None:
		     path = os.path.join(self.data_directory, df+'.hdf5')
		     print("Clock lock looking for file {}".format(path))
		     gnd, exc, background, ts = get_pmt_data(path)
		     pico_shot_range = np.arange(1, 150)
		     gnd_tot = np.sum((gnd - background)[pico_shot_range])
		     exc_tot = np.sum((exc - background)[pico_shot_range])
		    
		     print(gnd_tot, exc_tot)
		     atom_num = gnd_tot + exc_tot
		     exc_frac = float(exc_tot)/(exc_tot + gnd_tot)
		     
		     clock_phase = self.server.parameters.get('sequencer.clock_phase').value
		     print(clock_phase, exc_frac)
		     if clock_phase == .25 and self.errorSig != 0:
		     	self.errorSig += exc_frac
		     	out = self.PID.update(self.errorSig)
		     	print("new value: {}".format(out))
		     	self.server.parameters.get('clock_sg380').set_value_lock(out)
		     	self.errorSig = 0
		     	
		     if clock_phase == -.25:
    			self.errorSig -= exc_frac
    			


		     #self.server.parameters.get('clock_pulse_sg380').set_value_lock(out)


        #read data and get excitation fraction
        
        
        
        
        
    
Parameter = PmtLockChop
