import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

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
		plt.plot(t_split[i], split[i])
		plt.show()
		
		plt.figure()
		plt.plot(freqs, Pxx)
		plt.show()
		'''
		max_fs[i] = np.max(Pxx)
		arg = np.argmax(Pxx)
		print("Max freq: {}".format(freqs[arg]))
		
		t_avg[i] = np.mean(t_split[i])
	
	return t_avg, max_fs

def time_domain(data, dt):
	n_points = len(data)
	ts = np.arange(n_points)*dt
	return ts, data
    
   
    
    
    
    
    
    
