import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.stats import mode

n_split = 300  #400

def bin_data(data, ts, n_split):
	'''
	From John's jupyter notebooks
	'''
	dt = mode(np.diff(ts))[0][0]
	split = np.array_split(data, n_split)
	t_split = np.array_split(ts, n_split)
	t_avg = list(map(np.mean, t_split))
	return dt, split, t_split, t_avg
	

def show_fft(data, ts, t):
	dt, split, _, t_avgs = bin_data(data, ts, n_split)
	this_bin = np.argmin(np.abs(t_avgs - t))
	Pxx, freqs = mlab.psd(split[this_bin], NFFT = len(split[this_bin]), Fs = 1.0/dt, pad_to = 2**12)
	return Pxx, freqs, t_avgs[this_bin]

def find_VRS_peaks(max_fs, t_avg):
	cutoff_end = 50
	n_points = len(t_avg)
	ixs_lower, _ = find_peaks(-max_fs[:-cutoff_end, 0], distance = n_points/3)
	ixs_upper, _ = find_peaks(-max_fs[:-cutoff_end, 1], distance = n_points/3)
	#print(t_avg[ixs_lower])
	#print(t_avg[ixs_upper])

def find_cutoff(Pxx, freqs):
	ixs, prop = find_peaks(Pxx, height=(None, None))
	heights = prop['peak_heights']
	sorted_peaks = ixs[np.argsort(heights)]
	center = np.mean(freqs[sorted_peaks[-2:]])
	#print(freqs[sorted_peaks[-2:]])
	#print(center)
	return 2.96e+6#center
	

def do_two_tone(data, ts, n_split = n_split, show_cutoff = False, ix_cutoff = 0):
	#print(np.max(ts))
	dt, split, t_split, _= bin_data(data, ts, n_split)#n_bins hard-coded in rn!!	
	cutoff = 0
	max_fs = np.zeros((n_split, 2))
	f_vals = np.zeros((n_split, 2))
	ixs = np.insert(np.arange(n_split), 0, ix_cutoff)
	t_avg = np.zeros(n_split)	
	for j in np.arange(len(ixs)):
		i = ixs[j]
		Pxx, freqs = mlab.psd(split[i], NFFT = len(split[i]), Fs = 1.0/dt, pad_to = 2**12)
		if j ==0:
			cutoff = find_cutoff(Pxx, freqs)
			if show_cutoff:
				plt.figure()
				plt.plot(freqs, Pxx)			
				plt.axvline(cutoff, color='gray')
		lower = (freqs < cutoff) & (freqs > 1e+6)
		upper = freqs > cutoff
		max_fs[i, 0] = np.max(Pxx[lower])
		max_fs[i, 1] = np.max(Pxx[upper])
		f_vals[i, 0] = freqs[lower][np.argmax(Pxx[lower])]
		f_vals[i, 1] = freqs[upper][np.argmax(Pxx[upper])]        
		t_avg[i] = np.mean(t_split[i])
	n_points = len(t_avg)
	#find_VRS_peaks(max_fs, t_avg)
	return t_avg, max_fs #f_vals
	
def do_single_tone(data, ts):
	#print(np.max(ts))
	dt, split, t_split, _= bin_data(data, ts, n_split)#n_bins hard-coded in rn!!	
	cutoff = 0
	max_fs = np.zeros((n_split, 2))
	f_vals = np.zeros((n_split, 2))
	ixs = np.insert(np.arange(n_split), 0, 0)
	t_avg = np.zeros(n_split)	
	for j in np.arange(len(ixs)):
		i = ixs[j]
		Pxx, freqs = mlab.psd(split[i], NFFT = len(split[i]), Fs = 1.0/dt, pad_to = 2**12)
		#if j ==0:
		#	cutoff = find_cutoff(Pxx, freqs)
		#lower = (freqs < cutoff) & (freqs > 1e+6)
		cutoff = 1e6
		upper = freqs > cutoff
		lower_bound = int(1e6)
		max_fs[i, 0] = np.max(Pxx[upper])
		#max_fs[i, 1] = np.max(Pxx[upper])
		f_vals[i, 0] = freqs[np.argmax(Pxx[upper])]
		#f_vals[i, 1] = freqs[upper][np.argmax(Pxx[upper])]        
		t_avg[i] = np.mean(t_split[i])
	n_points = len(t_avg)
	#find_VRS_peaks(max_fs, t_avg)
	return t_avg, max_fs #f_vals	

def time_domain(data, ts):
	#n_points = len(data)
	#ts = np.arange(n_points)*dt
	return ts, data
    
def ones(data):
	#print(data)
	return 1
    
    
    
    
    
