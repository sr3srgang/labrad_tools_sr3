import numpy as np

this_expt = 'scan'

#Setting parameters for different classes of expts. 
f_cen = 116.55e6 + 8.2174e4

shotNum = 30

df_sb = 50e3
df_scan= 10
f_fixed = f_cen + 5

total_flopping_time = 12e-3 #TODO: add
default_t_pi = .4

default_int = .2


expt_types_values = {
	'sideband': {'clock_sg380': np.linspace(f_cen - df_sb, f_cen + df_sb, shotNum), 'sequencer.clock_int_pi': .6, 'sequencer.t_pi': .2},
	'scan': {'clock_sg380': np.linspace(f_cen - df_scan, f_cen + df_scan, shotNum), 'sequencer.clock_int_pi': default_int, 'sequencer.t_pi': default_t_pi},
	'fixed': {'clock_sg380': f_fixed, 'sequencer.clock_int_pi': default_int, 'sequencer.t_pi': default_t_pi},
	}



#Parameters shared by all expts:
freqCent_cleanup = f_cen
clock_int_cleanup = 0.1
cleanup_time = 0.045
clock_int_readout = .4
readout_time = .0052

shared_param_values = {
	'do_loop' : [0, 0],
	'clock_pulse_sg380': freqCent_cleanup,
	'sequencer.clock_int_cleanup': clock_int_cleanup,
	'sequencer.t_pi_cleanup': cleanup_time,
	'sequencer.clock_int_readout': clock_int_readout,
	'sequencer.t_pi_readout': readout_time,
	'sequencer.sequence': [
		'load_lattice_notrans_horizontal_mot_fluor_ver2',
		'ramp_fields_to_pol',
#		'optical_pump',
		'transport',
#		'ramp_lattice',
		'clock_pulse_pi',
		'gnd',
		'exc',
		'background']
	}
		
parameters = {
   'camera_recorder': {},
   'pico.clock_recorder': {},
   'si_demod': {},
   }


#Define expt to run:
parameter_values = shared_param_values
parameter_values.update(expt_types_values.get(this_expt))
from conductor.experiment import Experiment

my_experiment = Experiment(
        name='warmup_' + this_expt,
        parameters=parameters,
        parameter_values=parameter_values,
        loop=True,
        )
my_experiment.queue(run_immediately=True)
    
