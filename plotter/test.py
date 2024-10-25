import json
import numpy as np
import time

import labrad

from defaults import *
import defaults
reload(defaults)
print today
""" parameters here """
name = 'test'

run_immediately = True
loop = True

#Number of 4-points to cut at beginning and end for plot
cuts = (0, None) # Must be a tuple, otherwise you're f'ed

import os

#drift_settings = {
#    'drift_rate' : drift_rate,
#    'drift_time_initial' : drift_time_initial,
#    'drift_boolean' : drift_boolean,
#    'drift_dummy_freq' : drift_dummy_freq,
#}


plotter_settings = {
    #'plotter_path': '/media/j/notebooks/'+today+'/live_plotters/plot_density_shift.py',
    'plotter_path': 'home/srgang/labrad_tools/plotter/live_plotter/plot_test.py',
    'plotter_function': 'plot_test'
    }


parameters = {
    'plotter.plot': {}
    }

parameter_values = {
    'plotter.plot': json.dumps(plotter_settings),
        }

if __name__ == '__main__':
    from conductor.experiment import Experiment
    cxn = labrad.connect()
 #   request = {'sequencer.sequence':sequence_m}
 #   cxn.conductor.set_parameter_values(json.dumps(request))
    sleep(2)
    my_experiment = Experiment(
        name=name,
        parameters=parameters,
        parameter_values=parameter_values,
        loop=loop,
        )
    my_experiment.queue(run_immediately=run_immediately)
    
