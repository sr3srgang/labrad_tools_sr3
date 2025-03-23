import numpy as np

shotNum = 30
freqCent = 116.55e6 + 8.2174e4  # 78439.46
freqCent_cleanup = freqCent


# MM sideband scan params 20221208
# freqRan_wide = 35e3
# int_wide = .6
# t_pi_wide = .2


# rabi_scan_wide parameters: for warmup_wide.py
freqRan_wide = 10  # e3#10# .001#15 #20 #20#50 #10e3
int_wide = .2  # 1 #.2
t_pi_wide = .4  # .4#.005

# rabi_scan_narrow parameters: for warmup_narrow.py
freqRan_narrow = 20
int_narrow = .03
t_pi_narrow = .16


# rabi_flop parameters: for warmup_flop.py
total_flopping_time = 12e-3
int_flop = .4  # .1

# cleanup parameters
clock_int_cleanup = 0.1
cleanup_time = 0.045

# cleanup parameters
# clock_int_cleanup = 0.9
# cleanup_time = 0.059

# readout parameters
clock_int_readout = .4
readout_time = .0052
# readout parameters

# clock_int_readout = .9
# readout_time = .059

# CAVITY MEASUREMENT PARAMETERS
# UPDATE ME EACH DAY
# pi_time = .043#.0097##.0097#0.043#0.00514##
# clock_int = .1#.1#.1#.4
# parameter with ND filter
pi_time = 0.0053  # .042#.0097##.0097#0.043#0.00514##
clock_int = .4  # .1#.1#.4


align_phase = .25
clock_phase = .16
sweep_low = -1  # .05 #-.1
sweep_high = 1  # .45 #.4
slope_low = .15
slope_high = .19
fixed = 0.11  # .08#.16


# CLOCK PARAMS COMMON TO EACH EXPERIMENT
cav_clock_params = {

    'sequencer.clock_int': clock_int,
    'sequencer.clock_int_pi': clock_int,
    'sequencer.clock_int_readout': clock_int_readout,
    'sequencer.clock_int_cleanup': clock_int_cleanup,
    'sequencer.clock_int_align': clock_int,
    'sequencer.t_pi': pi_time,
    'sequencer.t_pi_cleanup': cleanup_time,
    'sequencer.t_pi_readout': readout_time,
    'sequencer.t_pi_2': pi_time/2,
    'sequencer.t_pi_2_align': pi_time/2,
    'sequencer.t_pi_2_cqed': pi_time/2,
    'sequencer.clock_phase_align': align_phase,
    'sequencer.t_dark': 0.04,
    # 'sequencer.t_cam_exposure': 0.0005,
    # 'sequencer.cav_eom_phase_sg380': 0,
    # 'sequencer.cav_eom_amp_sg380': -25,
    # 'sequencer.t_dark': np.linspace(0.01, 0.25,30)
}

# FORMATTING FOR EACH EXPERIMENT TYPE
# Ramsey parameters
ramsey_params = {
    'sequencer.clock_phase': np.linspace(-1, 1, 30),
    'sequencer.cav_sweep_ramsey_low': sweep_low,
    'sequencer.cav_sweep_ramsey_high': sweep_high,
    'sequencer.cav_sweep_low': fixed,
    'sequencer.cav_sweep_high': fixed,
}

# fixed parameters
fixed_params = {
    'sequencer.clock_phase': clock_phase,
    'sequencer.cav_sweep_ramsey_low': fixed,
    'sequencer.cav_sweep_ramsey_high': fixed,
    'sequencer.cav_sweep_low': fixed,
    'sequencer.cav_sweep_high': fixed,
}

# Slope parameters
slope_params = {
    'sequencer.clock_phase': clock_phase,
    'sequencer.cav_sweep_ramsey_low': slope_low,
    'sequencer.cav_sweep_ramsey_high': slope_high,
    'sequencer.cav_sweep_low': slope_low,
    'sequencer.cav_sweep_high': slope_high,
}

# Sweep parameters
sweep_params = {
    'sequencer.clock_phase': clock_phase,
    'sequencer.cav_sweep_ramsey_low': sweep_low,
    'sequencer.cav_sweep_ramsey_high': sweep_high,
    'sequencer.cav_sweep_low': sweep_low,
    'sequencer.cav_sweep_high': sweep_high,
    'sequencer.cav_sweep_ramsey_alt': fixed,
}
# John 0929 centering cav probe
center_params = {
    # 'sequencer.clock_phase': clock_phase,
}

cav_exp_params = {'ramsey': ramsey_params, 'fixed': fixed_params,
                  'slope': slope_params, 'sweep': sweep_params, 'center': center_params}
# wide sideband range, not updated but kept for reference
freqCent_sideband = freqCent
freqRan_sideband = 7000
shotNum_sideband = 20
