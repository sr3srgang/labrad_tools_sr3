# Relevant physical parameters
import numpy as np

freq_offset = 116.55e6
'''
<<<<<<< HEAD
pico_shot_range = np.arange(1, 120)
crossing_emp = .0027#-.0004
=======
'''
pico_shot_range = np.arange(2, 27)
crossing_emp = .0027  # -.0004
#>>>>>>> e6dd90e2f0d8b4ae18dafec1491a30094da08581
t_range_emp = [.00325, .020]
scan_rate_emp = 1e6/(20e-3)  # 1MHz/20 ms

no_atoms_thresh = 1.5
