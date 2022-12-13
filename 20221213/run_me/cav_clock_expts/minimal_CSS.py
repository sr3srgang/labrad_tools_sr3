import numpy as np
from defaults import *


minimal_CSS_parameter_values = {
    'sequencer.sequence': [
	'load_lattice_notrans_horizontal_mot_fluor_ver2',
#	'ramp_fields_to_pol',
	#'optical_pump',
	'transport',
	#'ramp_lattice',
	#'cleanup_pulse',
	#'clock_pulse_pi_2',
	
	
	#Readout: AUp, BUp, BDown, ADown
	'test_probe_alt',
	'clock_pulse_pi_cav', 
	'test_probe',

	#Fluorescence readout
	'gnd_coherent',
	'clock_pulse_pi_readout',
	'exc',
	'background',
	#bare cav shot at end
	#'cavity_sweep_once_without_trigger_homo_ramsey_strong_last'
	

        ],	
    'clock_sg380' : [freqCent, freqCent],
    'clock_pulse_sg380': freqCent_cleanup,
}
   
