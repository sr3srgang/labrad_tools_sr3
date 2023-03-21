import matplotlib.pyplot as plt
import numpy as np
import os, glob, h5py
import scipy.signal as signal
from scipy.optimize import minimize, curve_fit
cs = ['xkcd:bubblegum pink', 'xkcd:marigold', 'xkcd:celadon', 'xkcd:pale lilac']


def get_raw_datafiles(datapath, expt, pico_fmt):
    all_files = np.array(glob.glob(os.path.join(datapath, expt, pico_fmt.format('*'))))
    f_nums = np.array([int(f.split(expt+'/', 1)[1].split(".",1)[0]) for f in all_files])
    ix_sort = np.argsort(f_nums)
    return all_files[ix_sort], np.sort(f_nums)

def pull_files(datapath, expt, shot_nums = [[None, None]], cavity_fmt = '{}.cavity_probe_pico.hdf5', acc_fmt = None):
    
    if shot_nums[0][0] is None:
        shot_nums[0][0] = max(min(c_nums), min(a_nums))
    if shot_nums[0][1] is None:
        shot_nums[0][1] = min(max(c_nums), max(a_nums)) + 1
    all_cfs = []
    all_afs = []
    for shot_num in shot_nums:
        #Get relevant shots
        cav_files, c_nums = get_raw_datafiles(datapath, expt, cavity_fmt)
        cfs = cav_files[np.logical_and(c_nums >= shot_num[0], c_nums < shot_num[1])]
        all_cfs.extend(cfs)
        if acc_fmt is not None:
            acc_files, a_nums = get_raw_datafiles(datapath, expt, acc_fmt)
            afs = acc_files[np.logical_and(a_nums >= shot_num[0], a_nums < shot_num[1])]
            #assert len(cfs) == len(afs) == shot_nums[0][1] - shot_nums[0][0], "Data indexing messed up!!"
            all_afs.extend(afs)
    #if shot range not specified, use all data files. Assume standard python indexing fmt
   
    return all_cfs, all_afs

def read_file(f, trace = None):
    file = h5py.File(f)
    if trace is not None:
        return np.array(file[trace])
    else:
        ts = np.array(file['time'])
        trace_names = list(file.keys())
        trace_names.remove('time')
        all_traces = []
        for n in trace_names:
            all_traces.append(np.array(file[n]))
        return ts, trace_names, all_traces
    

def set_lowpass(voltage, sampling_rate, fc = 600, n_cut = 200):
    w = fc /(sampling_rate/2)
    b, a = signal.butter(1,w, 'lowpass', analog = False)
    output_V = signal.filtfilt(b, a, voltage)
    return signal.decimate(output_V[n_cut:], 13)

def get_lp_traces(f, lowpass = set_lowpass):
    ts, trace_names, all_traces = read_file(f)
    dt = np.median(np.diff(ts))
    lp_traces = [lowpass(tr, 1/dt) for tr in all_traces]
    ts_lp = np.linspace(min(ts), max(ts), len(lp_traces[0]))
    print(trace_names)
    return ts_lp, trace_names, lp_traces

def Q_fit(t, delta, A, kappa, c):
    x = (t - delta)/(kappa/2)
    return A* x/ (1 + x**2 ) + c

def lin_fit(t, m, b):
    return t*m + b

def process_shot_fit(file, fxn, p0, lp = set_lowpass, ax = None, colors = cs):
    ts, trace_names, all_traces = get_lp_traces(file)
    
    n_fits = len(all_traces)
    n_param = len(p0)
    fits = np.zeros((n_fits, n_param))
    fits_unc = np.zeros((n_fits, n_param))

    for j in np.arange(n_fits):
        #Leave option to not specity center point of crossing, and guess middle of time window
        if p0[0] is None:
            p0_j = [np.mean(ts)]
            p0_j.extend(p0[1:])
        else:
            p0_j = p0
            
        popt, pcov = curve_fit(fxn, ts, all_traces[j], p0 = p0_j)
        fits[j, :] = popt
        fits_unc[j, :] = np.sqrt(np.diag(pcov))
        
        if ax is not None:
            ax.plot(ts, all_traces[j], '.', color = colors[j], alpha = .1)
            ax.plot(ts, fxn(ts, *popt), color=colors[j], label = trace_names[j], linewidth = 3)
    print('ran fits')
    return fits, fits_unc

def process_shot_sweep(file, lp= set_lowpass, ax = None, colors = cs):
    return process_shot_fit(file, Q_fit, [None, 1, 10e-3, 0], lp = lp, ax = ax, colors = cs)


def jackknife_std(deltas):
    n_points, n_cols = deltas.shape
    n_reps = n_points
    stds = np.zeros((n_reps, n_cols))
    arr_points = np.arange(n_points)
    for i in np.arange(n_reps):
        np.random.shuffle(arr_points)
        stds[i, :] = np.std(deltas[arr_points < n_points*.8, :], 0)
    return np.mean(stds, 0), np.std(stds, 0)


