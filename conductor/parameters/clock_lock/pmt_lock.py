import json
import os
import time
from data_analysis.cavity_clock.read_data import *
from data_analysis.cavity_clock.helpers import *
from twisted.internet import reactor
from conductor.parameter import ConductorParameter
from data_analysis.PID import PID


class PmtLock(ConductorParameter):
    autostart = False
    priority = 10
    data_directory = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    #data_filename = '{}.conductor.json'
    call_in_thread = False

    def initialize(self, config):
        super(PmtLock, self).initialize(config)
        self.connect_to_labrad()
        self.PID_params = {"k_prop": .5, "t_int": 50, "t_diff": 0, "setpoint":.5,  "dt": 3, "output_default":116.2614585*1e6}
        self.PID = PID(self.PID_params)
        self.server.parameters.get('clock_sg380').set_value_lock(116.2614585e6)
        print('Running a pmt clock lock')
        
    def update(self):
        print('Lock update at {}'.format(time.time()))
        #Data file to use:
        df = self.server.parameters.get('pico.clock_recorder').get_last_value() #want to find the data file from last shot during this blue mot loading
        if df is not None:
             path = os.path.join(self.data_directory, df+'.hdf5')
             print("Clock lock looking for file {}".format(path))
             gnd, exc, background, freq, _, shot_num, t_dark = get_clock_data(path, time_name = 'shot_num')
             pico_shot_range = np.arange(6, 25)
             gnd_tot = np.sum((gnd - background)[pico_shot_range])
             exc_tot = np.sum((exc - background)[pico_shot_range])
            
             print(gnd_tot, exc_tot)
             atom_num = gnd_tot + exc_tot
             exc_frac = float(exc_tot)/(exc_tot + gnd_tot)
             err_sig = exc_frac
             print(exc_frac)
             
             out = self.PID.update(err_sig)
             print(out)
             
             self.server.parameters.get('clock_sg380').set_value_lock(out)

        #read data and get excitation fraction
        
        
        
        
        
    
Parameter = PmtLock