import os, json, glob, h5py, scipy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from scipy import signal
from scipy.optimize import curve_fit


from data_analysis.pico import bin_data, find_cutoff

def set_rf_sweep(dict_vals, i = 0):
    globals().update(dict_vals)
    data_format = data_format_gen(df)
    file = h5py.File(data_format(i))
    data = np.array(file['gnd'])
    ts = np.array(file['time'])
    t_avg, f_vals = get_res_fs(ts, data)
    
    ix_avg_0 = in_peak(t_avg, p0)
    ix_0 = in_peak(ts, p0)
    rf0l, rf0h = fit_res_fs(t_avg[ix_avg_0], f_vals[ix_avg_0], ts[ix_0])
        
    ix_avg_1 = in_peak(t_avg, p1)
    ix_1 = in_peak(ts, p1)
    rf1l, rf1h = fit_res_fs(t_avg[ix_avg_1], f_vals[ix_avg_1], ts[ix_1])
    
    fig = plt.figure()
    fig.set_size_inches(12, 6)
    plt.plot(t_avg, f_vals[:, 0], '.', alpha = .05, c = 'xkcd:bubblegum pink')
    plt.plot(t_avg, f_vals[:, 1], '.', alpha = .05, c = 'xkcd:marigold')
    plt.plot(ts[ix_0], rf0l, 'xkcd:barbie pink')
    plt.plot(ts[ix_0], rf0h, 'xkcd:tangerine')
    plt.plot(ts[ix_1], rf1l, 'xkcd:barbie pink')
    plt.plot(ts[ix_1], rf1h, 'xkcd:tangerine') 
    plt.ylim(bounds[0], bounds[1])
    plt.show()
    
    return {'rfs':[rf0l, rf0h, rf1l, rf1h], 'ixs': [ix_0, ix_0, ix_1, ix_1]}

def get_res_fs(ts, data, n_split = 150, ix_cutoff = 0):
	#print(np.max(ts))
	dt, split, t_split, _= bin_data(data, ts, n_split)   
	f_vals = np.zeros((n_split, 2))
	ixs = np.insert(np.arange(n_split), 0, ix_cutoff)
	t_avg = np.zeros(n_split)
    #Using two-tone style analysis to fix rf tones
	for j in np.arange(len(ixs)):
		i = ixs[j]
		Pxx, freqs = mlab.psd(split[i], NFFT = len(split[i]), Fs = 1.0/dt)
        #we use bin number ix_cutoff to separate the higher/lower sidebands
		if j ==0:
			cutoff = find_cutoff(Pxx, freqs)
			plt.figure()
			plt.plot(freqs, Pxx)
			plt.xlim(1e6, 5e6)
			plt.show()
		lower = (freqs < cutoff) & (freqs > 1e+6)
		upper = freqs > cutoff
		f_vals[i, 0] = freqs[lower][np.argmax(Pxx[lower])]
		f_vals[i, 1] = freqs[upper][np.argmax(Pxx[upper])]
		t_avg[i] = np.mean(t_split[i])
	return t_avg, f_vals

def get_res_fs_single(ts, data, n_split = 150):
    	#print(np.max(ts))
	dt, split, t_split, _= bin_data(data, ts, n_split)   
	f_vals = np.zeros(n_split)
	t_avg = np.zeros(n_split)
    #Using single-tone style analysis to fix rf tone
	plt.figure()
	for i in np.arange(n_split):
		Pxx, freqs = mlab.psd(split[i], NFFT = len(split[i]), Fs = 1.0/dt)
		if i %10 ==0:
			plt.plot(freqs, Pxx)
			plt.xlim(bounds[0], bounds[1])
		filtered = (freqs > bounds[0])
		f_vals[i] = freqs[filtered][np.argmax(Pxx[filtered])]
		t_avg[i] = np.mean(t_split[i])
	plt.show
	return t_avg, f_vals

def set_rf_sweep_single(dict_vals, i = 0):
    globals().update(dict_vals)
    data_format = data_format_gen(df)
    file = h5py.File(data_format(i))
    data = np.array(file['gnd'])
    ts = np.array(file['time'])
    t_avg, f_vals = get_res_fs_single(ts, data)
    
    ix_avg_0 = in_peak(t_avg, p0)
    ix_0 = in_peak(ts, p0)
    rf0 = fit_res_fs_single(t_avg[ix_avg_0], f_vals[ix_avg_0], ts[ix_0])
        
    ix_avg_1 = in_peak(t_avg, p1)
    ix_1 = in_peak(ts, p1)
    rf1 = fit_res_fs_single(t_avg[ix_avg_1], f_vals[ix_avg_1], ts[ix_1])
    
    fig = plt.figure()
    fig.set_size_inches(12, 6)
    plt.plot(t_avg, f_vals, '.', alpha = .05, c = 'xkcd:bubblegum pink')
    plt.plot(ts[ix_0], rf0, 'xkcd:barbie pink')
    plt.plot(ts[ix_1], rf1, 'xkcd:barbie pink')
    plt.ylim(bounds[0], bounds[1])
    plt.show()
    
    return {'rfs':[rf0, rf1], 'ixs': [ix_0, ix_1]}

def fit_res_fs(t_avg, f_vals, ts_full):
    ok = np.logical_and(f_vals> bounds[0], f_vals <bounds[1])
    ok = np.logical_and(ok[:, 0], ok[:, 1])
    t_avg = t_avg[ok]
    f_vals = f_vals[ok, :]
   
    def sweep_form(t, m, b):
        return t*m + b
    popt0, _ = curve_fit(sweep_form, t_avg, f_vals[:, 0])
    popt1, _ = curve_fit(sweep_form, t_avg, f_vals[:, 1])
    
    #second round of filtering to remove outlier points
    cutoff = 4e4
    ok = np.logical_and(np.abs(f_vals[:, 0] - sweep_form(t_avg, *popt0)) < cutoff, np.abs(f_vals[:, 1] - sweep_form(t_avg, *popt1)) < cutoff)
    t_avg = t_avg[ok]
    f_vals = f_vals[ok]
    popt0, _ = curve_fit(sweep_form, t_avg, f_vals[:, 0])
    popt1, _ = curve_fit(sweep_form, t_avg, f_vals[:, 1])
    y0 = sweep_form(ts_full, *popt0)
    y1 = sweep_form(ts_full, *popt1)
    return y0, y1

def fit_res_fs_single(t_avg, f_vals, ts_full):
    ok = np.logical_and(f_vals> bounds[0], f_vals <bounds[1])
    t_avg = t_avg[ok]
    f_vals = f_vals[ok]
   
    def sweep_form(t, m, b):
        return t*m + b
    popt0, _ = curve_fit(sweep_form, t_avg, f_vals)
    
    #second round of filtering to remove outlier points
    cutoff = 4e4
    ok = np.abs(f_vals - sweep_form(t_avg, *popt0)) < cutoff
    t_avg = t_avg[ok]
    f_vals = f_vals[ok]
    popt0, _ = curve_fit(sweep_form, t_avg, f_vals)
    y0 = sweep_form(ts_full, *popt0)
    return y0

def do_iq_fixed(ts, data, omega_rf):
    dt = np.median(np.diff(ts))
    phi_t = np.cumsum(omega_rf)*dt
    
    V_c = np.cos(phi_t)*data
    V_s = np.sin(phi_t)*data
    
    #filtering,
    #Design of digital filter requires cut-off frequency to be normalised by sampling_rate/2
    fc = 500
    w = fc /(1/dt/2)
    b, a = signal.butter(2, w, 'low', analog = False)
    V_c = signal.filtfilt(b, a, V_c)
    V_s = signal.filtfilt(b, a, V_s)
    
    #downsample 4x for each signal:
    signals = [V_c, V_s, ts, omega_rf]
    sampled = [scipy.signal.decimate(scipy.signal.decimate(scipy.signal.decimate(scipy.signal.decimate(sig, 10), 10), 10), 10) for sig in signals]

    return sampled
    
def fixed_tone_avg_phase(fname, omegaBeat, t_ranges):
    f = h5py.File(fname)
    data = np.array(f['gnd'])
    ts = np.array(f['time'])
    
    n_segments = len(t_ranges)
    avg_phi = np.zeros(n_segments)
    
    for i in n_segments:
    	ix_start = np.argmin(np.abs(ts - t_ranges[i][0]))
    	ix_end = np.argmin(np.abs(ts - t_ranges[i][1]))
    	these_ts = ts[ix_start:ix_end]
    	these_data = data[ix_start:ix_end]
    	omegas = omegaBeat*np.ones(len(these_ts))
    	sampled = do_iq_fixed(these_ts, these_data, omegas)
    	phi = np.unwrap(np.arctan2(sampled[1], sampled[0]))
    	avg_phi[i] = np.mean(phi)
    
    return avg_phi
    
    
     
