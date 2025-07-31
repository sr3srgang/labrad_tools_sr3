import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import h5py
import scipy.signal as signal
from scipy.optimize import minimize, curve_fit
# ['xkcd:bubblegum pink', 'xkcd:marigold', 'xkcd:celadon', 'xkcd:pale lilac']
# cs = ['white', 'k', 'white', 'k', 'white', 'k', 'gray']
xkcd_cs = ['hot magenta', 'orangered', 'manilla',
           'kiwi green', 'azul', 'vivid purple']
cs = ['xkcd:'+c for c in xkcd_cs]
styles = ['-', '--', '-.']
c_bkgd = 'xkcd:grey'
# cs = ['white', 'k', 'blue', 'brown', 'green',
#       'white', 'k', 'blue', 'brown', 'green', 'gray']
# styles = ['--', '--', '--', '--', '--', '-', '-', '-', '-', '-', '-.']
# styles = ['--', '--', '-.', '-.', '-', '-', '-', '-', '-', '-', '-']
p0_fixed = [0]
p0_Q = [None, 1, 10e-3, 0]


def get_raw_datafiles(datapath, expt, pico_fmt):
    all_files = np.array(glob.glob(os.path.join(
        datapath, expt, pico_fmt.format('*'))))
    f_nums = np.array([int(f.split(expt+'/', 1)[1].split(".", 1)[0])
                      for f in all_files])
    ix_sort = np.argsort(f_nums)
    return all_files[ix_sort], np.sort(f_nums)


def pull_files(datapath, expt, shot_nums=[[None, None]], cavity_fmt='{}.cavity_probe_pico.hdf5', acc_fmt=None):

    if shot_nums[0][0] is None:
        shot_nums[0][0] = max(min(c_nums), min(a_nums))
    if shot_nums[0][1] is None:
        shot_nums[0][1] = min(max(c_nums), max(a_nums)) + 1
    all_cfs = []
    all_afs = []
    for shot_num in shot_nums:
        # Get relevant shots
        cav_files, c_nums = get_raw_datafiles(datapath, expt, cavity_fmt)
        cfs = cav_files[np.logical_and(
            c_nums >= shot_num[0], c_nums < shot_num[1])]
        all_cfs.extend(cfs)
        if acc_fmt is not None:
            acc_files, a_nums = get_raw_datafiles(datapath, expt, acc_fmt)
            afs = acc_files[np.logical_and(
                a_nums >= shot_num[0], a_nums < shot_num[1])]
            # assert len(cfs) == len(afs) == shot_nums[0][1] - shot_nums[0][0], "Data indexing messed up!!"
            all_afs.extend(afs)
    # if shot range not specified, use all data files. Assume standard python indexing fmt

    return all_cfs, all_afs


def read_file(f, trace=None):
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


def set_lowpass(voltage, sampling_rate, fc=600, n_cut=200):
    w = fc / (sampling_rate/2)
    b, a = signal.butter(1, w, 'lowpass', analog=False)
    output_V = signal.filtfilt(b, a, voltage)
    return signal.decimate(output_V[n_cut:], 13)


def get_lp_traces(f, lowpass=set_lowpass):
    ts, trace_names, all_traces = read_file(f)
    dt = np.median(np.diff(ts))
    lp_traces = [lowpass(tr, 1/dt) for tr in all_traces]
    ts_lp = np.linspace(min(ts), max(ts), len(lp_traces[0]))
    return ts_lp, trace_names, lp_traces


def Q_fit(t, delta, A, kappa, c):
    x = (t - delta)/(kappa/2)
    return A * x / (1 + x**2) + c


def Q_fit_slope(t, delta, A, kappa, c):
    x = (t - delta)/(kappa/2)
    return -2*A/kappa * (x**2 - 1)/(1 + x**2)**2


def lin_fit(t, m, b):
    return t*m + b


def fixed_fit(t, b):
    return t*0 + b


def process_shot_fit(file, fxn, p0, lp=set_lowpass, ax=None, colors=cs, c_bkgd=c_bkgd, styles=styles, fit_exclude=.001):
    ts, trace_names, all_traces = get_lp_traces(file)
    # MM added 20230323 to exclude transient beginning/end behavior from fit. To remove, set fit_exclude = 0.
    fit_ix = np.logical_and(ts > fit_exclude, ts < max(ts) - fit_exclude)

    n_fits = len(all_traces)
    # MM 20230424 assuming Q-fit is most complex we'll be doing, and there might be some fixed meas. too
    if type(fxn) is not list:
        fxn = [fxn]*n_fits
        p0 = [p0]*n_fits

    n_param = 4
    fits = np.zeros((n_fits, n_param))
    fits_unc = np.zeros((n_fits, n_param))

    for j in np.arange(n_fits):
        # Leave option to not specity center point of crossing, and guess middle of time window
        if p0[j][0] is None:
            p0_j = [np.mean(ts)]
            p0_j.extend(p0[j][1:])
        else:
            p0_j = p0[j]
        ts_fit = ts[fit_ix]
        popt, pcov = curve_fit(fxn[j], ts_fit, all_traces[j][fit_ix], p0=p0_j)
        fits[j, 0:len(popt)] = popt
        fits_unc[j, 0:len(popt)] = np.sqrt(np.diag(pcov))
        h_offset = 0  # max(ts)*j
        v_offset = 0  # .05*j
        if ax is not None:
            if j == n_fits - 1:
                c = c_bkgd
                s = styles[0]
            else:
                c = colors[j % len(colors)]
                s = styles[int(j/len(colors))]
            if c != 'red':
                ax.plot((ts + h_offset)*1e3,
                        all_traces[j] + v_offset, 'o', color=c, markersize=1, alpha=.1)
                ax.plot((ts_fit + h_offset)*1e3, fxn[j](ts_fit, *popt) + v_offset,
                        s, color=c, label=trace_names[j], linewidth=1)
            ax.set_xlabel('Time (ms)')
    return fits, fits_unc


def process_shot_1ens(file, lp=set_lowpass, ax=None, colors=cs):
    fxns = [fixed_fit, fixed_fit, fixed_fit, Q_fit, fixed_fit, Q_fit, Q_fit]

    p0s = [p0_fixed, p0_fixed, p0_fixed, p0_Q, p0_fixed, p0_Q, p0_Q]
    return process_shot_fit(file,  fxns, p0s, lp=lp, ax=ax, colors=colors)


def process_shot_sweep(file, lp=set_lowpass, ax=None, colors=cs):
    return process_shot_fit(file, Q_fit, [None, 1, 10e-3, 0], lp=lp, ax=ax, colors=colors)


def process_shot_var(file, fixed_ixs, lp=set_lowpass, ax=None, colors=cs):
    fxns = []
    p0s = []
    for i in np.arange(len(fixed_ixs)):
        if fixed_ixs[i]:
            fxns.append(fixed_fit)
            p0s.append(p0_fixed)
        else:
            fxns.append(Q_fit)
            p0s.append(p0_Q)

    return process_shot_fit(file,  fxns, p0s, lp=lp, ax=ax, colors=colors)


def jackknife_std(deltas, rng=.8):
    n_points, n_cols = deltas.shape
    n_reps = n_points
    stds = np.zeros((n_reps, n_cols))
    arr_points = np.arange(n_points)
    for i in np.arange(n_reps):
        np.random.shuffle(arr_points)
        stds[i, :] = np.std(deltas[arr_points < n_points*rng, :], 0)
    return np.mean(stds, 0), np.std(stds, 0)


def get_windows(seq):
    # MM 20230508, assuming windows either sweep or fix, returns fixed indices. to be used w/ process_shot_var
    cav_seq = [s for s in seq if "cav_" in s]
    return ["fixed" in s for s in cav_seq]
