import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import h5py
import scipy.signal as signal
from scipy.optimize import curve_fit

plt.rcParams.update({'font.size': 18})
plt.rcParams['image.cmap'] = 'turbo'

# Initial parameters for fitting
p0_fixed = [0]
p0_Q = [0.018, -0.15, 4e-3, 0]

def get_raw_datafiles(datapath, expt, pico_fmt):
    """Retrieve and sort raw data files."""
    all_files = np.array(glob.glob(os.path.join(datapath, expt, pico_fmt.format('*'))))
    f_nums = np.array([int(f.split(expt+'/', 1)[1].split(".", 1)[0]) for f in all_files])
    ix_sort = np.argsort(f_nums)
    return all_files[ix_sort], np.sort(f_nums)

def pull_files(datapath, expt, shot_nums=[[None, None]], cavity_fmt='{}.cavity_probe_pico.hdf5', acc_fmt=None):
    """Pull and sort files based on shot numbers."""
    cav_files, c_nums = get_raw_datafiles(datapath, expt, cavity_fmt)
    acc_files, a_nums = None, None
    if acc_fmt is not None:
        acc_files, a_nums = get_raw_datafiles(datapath, expt, acc_fmt)

    if shot_nums[0][0] is None:
        shot_nums[0][0] = max(min(c_nums), min(a_nums) if a_nums is not None else float('inf'))
    if shot_nums[0][1] is None:
        shot_nums[0][1] = min(max(c_nums), max(a_nums) if a_nums is not None else float('-inf')) + 1

    all_cfs, all_afs = [], []
    for shot_num in shot_nums:
        cfs = cav_files[np.logical_and(c_nums >= shot_num[0], c_nums < shot_num[1])]
        all_cfs.extend(cfs)
        if acc_files is not None:
            afs = acc_files[np.logical_and(a_nums >= shot_num[0], a_nums < shot_num[1])]
            all_afs.extend(afs)

    return all_cfs, all_afs

def read_file(file, trace=None):
    """Read data from an HDF5 file."""
    with h5py.File(file, 'r') as f:
        if trace is not None:
            return np.array(f[trace])
        else:
            ts = np.array(f['time'])
            trace_names = list(f.keys())
            trace_names.remove('time')
            all_traces = [np.array(f[n]) for n in trace_names]
            return ts, trace_names, all_traces

def set_lowpass(voltage, sampling_rate, fc=600, n_cut=200):
    """Apply a lowpass filter and decimate the signal."""
    w = fc / (sampling_rate / 2)
    b, a = signal.butter(1, w, 'lowpass', analog=False)
    output_V = signal.filtfilt(b, a, voltage)
    return signal.decimate(output_V[n_cut:], 13)

def get_lp_traces(file, lowpass=set_lowpass):
    """Get lowpass filtered traces from a file."""
    ts, trace_names, all_traces = read_file(file)
    dt = np.median(np.diff(ts))
    lp_traces = [lowpass(tr, 1/dt) for tr in all_traces]
    ts_lp = np.linspace(min(ts), max(ts), len(lp_traces[0]))
    return ts_lp, trace_names, lp_traces

def Q_fit(t, delta, A, kappa, c):
    """Function for Q factor fitting."""
    x = (t - delta) / (kappa / 2)
    return A * x / (1 + x**2) + c

def Q_fit_slope(t, delta, A, kappa, c):
    """Function for the slope of Q factor fit."""
    x = (t - delta) / (kappa / 2)
    return -2 * A / kappa * (x**2 - 1) / (1 + x**2)**2

def lin_fit(t, m, b):
    """Linear fit function."""
    return t * m + b

def fixed_fit(t, b):
    """Fixed fit function."""
    return t * 0 + b

def process_shot_plot(file, fxn, lp=set_lowpass, ax=None, fit_exclude=0.003):
    """Process and fit a shot data file."""
    ts, trace_names, all_traces = get_lp_traces(file)
    fit_ix = np.logical_and(ts > fit_exclude, ts < max(ts) - fit_exclude)

    n_param = 4

    for j in range(len(all_traces)):

        if ax is not None:
            ax.plot(ts * 1e3, all_traces[j], '.', markersize=0.5, alpha=0.1)
            style = '--' if j < 2 else '-'
            ax.set_xlabel('Time (ms)')
    return ts, all_traces

def process_shot_fit(file, fxn, p0, lp=set_lowpass, ax=None, fit_exclude=0.003):
    """Process and fit a shot data file."""
    ts, trace_names, all_traces = get_lp_traces(file)
    fit_ix = np.logical_and(ts > fit_exclude, ts < max(ts) - fit_exclude)

    if not isinstance(fxn, list):
        fxn = [fxn] * len(all_traces)
        p0 = [p0] * len(all_traces)

    n_param = 4
    fits = np.zeros((len(all_traces), n_param))
    fits_unc = np.zeros((len(all_traces), n_param))

    for j in range(len(all_traces)):
        p0_j = [np.mean(ts)] + p0[j][1:] if p0[j][0] is None else p0[j]
        ts_fit = ts[fit_ix]
        popt, pcov = curve_fit(fxn[j], ts_fit, all_traces[j][fit_ix], p0=p0_j)
        fits[j, :len(popt)] = popt
        fits_unc[j, :len(popt)] = np.sqrt(np.diag(pcov))

        if ax is not None:
            ax.plot(ts * 1e3, all_traces[j], '.', markersize=0.5, alpha=0.1)
            style = '--' if j < 2 else '-'
            ax.plot(ts_fit * 1e3, fxn[j](ts_fit, *popt), style, label=trace_names[j], linewidth=1)
            ax.set_xlabel('Time (ms)')

    return fits, fits_unc

def process_shot_1ens(file, lp=set_lowpass, ax=None):
    """Process a single ensemble shot."""
    fxns = [fixed_fit, fixed_fit, fixed_fit, Q_fit, fixed_fit, Q_fit, Q_fit]
    p0s = [p0_fixed, p0_fixed, p0_fixed, p0_Q, p0_fixed, p0_Q, p0_Q]
    return process_shot_fit(file, fxns, p0s, lp=lp, ax=ax)

def process_shot_sweep(file, lp=set_lowpass, ax=None):
    """Process a shot sweep."""
    return process_shot_fit(file, Q_fit, [None, 1, 10e-3, 0], lp=lp, ax=ax)

def process_shot_var(file, fixed_ixs, lp=set_lowpass, ax=None):
    """Process a shot with variable fits."""
    fxns = [fixed_fit if fixed else Q_fit for fixed in fixed_ixs]
    p0s = [p0_fixed if fixed else p0_Q for fixed in fixed_ixs]
    return process_shot_fit(file, fxns, p0s, lp=lp, ax=ax)

def jackknife_std(deltas, rng=0.8):
    """Compute jackknife standard deviation."""
    n_points, n_cols = deltas.shape
    stds = np.zeros((n_points, n_cols))
    arr_points = np.arange(n_points)
    for i in range(n_points):
        np.random.shuffle(arr_points)
        stds[i, :] = np.std(deltas[arr_points < n_points * rng], axis=0)
    return np.mean(stds, axis=0), np.std(stds, axis=0)

def get_windows(seq):
    """Determine fixed windows from sequence."""
    cav_seq = [s for s in seq if "cav_" in s]
    return ["fixed" in s for s in cav_seq]