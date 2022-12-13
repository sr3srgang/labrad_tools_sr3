import json
import labrad
import numpy as np

parameters = {
    }
    
parameter_values = {
    'sequencer.sequence': [
        'all_off'
        ]
    }

#cxn = labrad.connect()
#cxn.conductor.set_parameter_values(json.dumps(parameter_values))
from conductor.experiment import Experiment

my_experiment = Experiment(
        name = 'end_expt',
        parameters = parameters,
        parameter_values = parameter_values,
        loop = False
        )

my_experiment.queue(run_immediately=True)
