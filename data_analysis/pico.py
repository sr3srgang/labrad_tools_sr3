import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.stats import mode

def do_binned_fft(data, dt):
	'''
	From John's jupyter notebooks
	'''
	n_split = 500 #this shouldn't be permanently hard-coded in!!
	split = np.array_split(data, n_split)
	max_fs = np.zeros(n_split)
	
	n_points = len(data)
	ts = np.arange(n_points)*dt
	t_split = np.array_split(ts, n_split)
	t_avg = np.zeros(n_split)
	
	for i in np.arange(n_split):
		Pxx, freqs = mlab.psd(split[i], NFFT = len(split[i]), Fs = 1.0/dt, pad_to = 2**12)

		'''
		plt.figure()
		plt.plot(freqs, Pxx)
		plt.show()
'''
		max_fs[i] = np.max(Pxx)
		arg = np.argmax(Pxx)
		print("Max freq: {}".format(freqs[arg]))
		
		t_avg[i] = np.mean(t_split[i])
	
	return t_avg, max_fs

def show_fft(data, ts, t):
	Pxx, freqs = mlab.psd(split[i], NFFT = len(split[i]), Fs = 1.0/dt, pad_to = 2**12)
		
def do_two_tone(data, ts):
	'''
	From John's jupyter notebooks
	'''
	dt = mode(np.diff(ts))[0][0]
	print(dt)
	n_split =500#this shouldn't be permanently hard-coded in!!
	cutoff = 3833878.186334917 #or this!!
	split = np.array_split(data, n_split)
	max_fs = np.zeros((n_split, 2))
	f_vals = np.zeros((n_split, 2))
	n_points = len(data)
	#ts = np.arange(n_points)*dt
	t_split = np.array_split(ts, n_split)
	t_avg = np.zeros(n_split)
	
	for i in np.arange(n_split):
		Pxx, freqs = mlab.psd(split[i], NFFT = len(split[i]), Fs = 1.0/dt, pad_to = 2**12)
		lower = (freqs < cutoff) & (freqs > 1e+6)
		upper = freqs > cutoff
		max_fs[i, 0] = np.max(Pxx[lower])
		max_fs[i, 1] = np.max(Pxx[upper])
		f_vals[i, 0] = freqs[lower][np.argmax(Pxx[lower])]
		f_vals[i, 1] = freqs[upper][np.argmax(Pxx[upper])]        
		'''plt.figure()
		plt.plot(freqs, Pxx)
		plt.show()'''
		t_avg[i] = np.mean(t_split[i])
	n_points = len(t_avg)
	cutoff_end = 50
	ixs_lower, _ = find_peaks(-max_fs[:-cutoff_end, 0], distance = n_points/3)
	ixs_upper, _ = find_peaks(-max_fs[:-cutoff_end, 1], distance = n_points/3)
	print(t_avg[ixs_lower])
	print(t_avg[ixs_upper])
	return t_avg, max_fs #f_vals
def time_domain(data, ts):
	#n_points = len(data)
	#ts = np.arange(n_points)*dt
	return ts, data
    
   
    
    
    
    
    
    
