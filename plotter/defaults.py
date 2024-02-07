# Load some modules needed for all scripts
import json
import numpy as np
import os
import labrad
from time import sleep

today = '20210621'

#zero
f_zero =  -235616938.7933

f_right =  -235616934.075
f_left  =  -235616943.556

# set mF clock frequency to  be the same as f_zero
# takes care of fnc and f_sterr being different
#Set to -1 if you want to lock to servo points!
f_mF =  f_zero  #f_zero

f_probe = (f_left+f_right)/2
zeeman_shift = (f_right-f_left)/2. #added -1 for DC stark

#Dedrift params
drift_rate = 0.0000
drift_time_initial =  1615234462.5
drift_boolean = False
drift_dummy_freq = 176.724912e6

#offsets for ac stark shift (low lattice case)
#f_center_offset = 0 #1.0
#zeeman_offset = 0 #1.0

#overwrite
#zeeman_shift = 0.
#f_probe = f_left # - 20.e3

rabi_time = 2.5

range_in_linewidths = 400
steps_per_linewidth = 1
linewidth = 0.05
