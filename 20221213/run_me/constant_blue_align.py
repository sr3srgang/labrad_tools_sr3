import json
import labrad
import numpy as np

parameters = {
    }
    
parameter_values = {
    'sequencer.sequence': [
	#'part1',
	#'part2',
        'constant_blue_align_horizontal_mot_vertical_mot_fluor',
#        'axial_cooling',
        #'3P2_horizontal_mot_vertical_mot_fluor',
        ],
    }

cxn = labrad.connect()
cxn.conductor.set_parameter_values(json.dumps(parameter_values))
