import json
import labrad
import numpy as np
#test
parameters = {
    }
    
parameter_values = {
    'sequencer.sequence': [
	#'part1',
	#'part2',
        'all_off',
        ],
    }

cxn = labrad.connect()
cxn.conductor.set_parameter_values(json.dumps(parameter_values))
