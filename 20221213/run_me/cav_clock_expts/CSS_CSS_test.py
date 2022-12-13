import numpy as np
from defaults import *


CSS_CSS_parameter_values = {
    'sequencer.sequence': [
	'load_lattice_notrans_horizontal_mot_fluor_ver2',
	'ramp_fields_to_pol',
	'optical_pump',
	'transport',
	'ramp_lattice',
	'cleanup_pulse',
	'clock_pulse_pi_2',
	
	
	#Prepare CSS vs CSS: noAUp, noBUp, noADown, noBDown
#	'test_noprobe_withtrigger',
	#'test_probe_alt',
	'transport_small_down',
	'test_probe',
	'transport_small_up',
	'clock_pulse_pi_cav',
	'test_probe',
	'transport_small_down',
	'test_probe',
	'transport_small_up',



	#Ramsey evolution
	'clock_pulse_pi_2_align_nopulse',
	'dark_time_cav',
	'clock_pulse_pi_2_cqed_cav_nopulse',


	#Readout: AUp, BUp, BDown, ADown

#	'cavity_sweep_once_without_trigger_homo_ramsey_strong',
#	'transport_small_down',
#	'cavity_sweep_once_without_trigger_homo_ramsey_strong',
	'clock_pulse_pi_cav',
	'cavity_sweep_once_without_trigger_homo_ramsey_strong',
	'transport_small_up',
#	'cavity_sweep_once_without_trigger_homo_ramsey_strong_last',

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
   
