import numpy as np
from defaults import cav_clock_params, cav_exp_params
from CSS_CSS_test import CSS_CSS_parameter_values
from minimal_CSS import minimal_CSS_parameter_values

sequence_param_values = {
	'CSS_CSS':CSS_CSS_parameter_values,
	'minimal_CSS': minimal_CSS_parameter_values
	}
	
parameters = {
    'camera_recorder': {},
    }
      
from conductor.experiment import Experiment

states = 'minimal_CSS'
exp = 'sweep'

parameter_values = cav_clock_params
parameter_values.update(sequence_param_values.get(states))
parameter_values.update(cav_exp_params.get(exp))

my_experiment = Experiment(
        name=states + '_' + exp,
        parameters=parameters,
        parameter_values=parameter_values,
        loop=True,
        )
my_experiment.queue(run_immediately=True)
