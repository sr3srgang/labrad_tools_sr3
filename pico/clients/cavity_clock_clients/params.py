# Relevant physical parameters
import numpy as np

freq_offset = 116.55e6
pico_shot_range = np.arange(1, 150)
crossing_emp = .0027  # -.0004

t_range_emp = [.00325, .020]
scan_rate_emp = 1e6/(20e-3)  # 1MHz/20 ms

no_atoms_thresh = 1.5
