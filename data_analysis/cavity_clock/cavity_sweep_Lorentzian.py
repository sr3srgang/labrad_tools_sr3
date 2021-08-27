import matplotlib.pyplot as plt
import os, json
import numpy as np
import matplotlib.pyplot as plt
from pico.clients.cavity_clock_clients.listeners import get_cavity_data, get_vrs, get_res_dips, do_moving_avg
from data_analysis.pico import do_two_tone, n_split

import numpy as np

#For doing Lorentzian fits of two tone cavity probing: 
def skew_L(x, x0, Gamma, A, B, C):
    #normalized s.t. max value is A, and superimposed on linear slope
    return A*(Gamma/2)**2/((x - x0)**2 + (Gamma/2)**2) + B*(x - x0) + C

def fit_L(raw_fs, ax):
    x, fs = do_moving_avg(t_avg, raw_fs, 5)
    
    #Find region of minimum past crossing
    crossing_ix = np.argmin(np.abs(x - crossing_emp))
    
    j_smooth = np.argmin(fs[x > crossing_emp]) + crossing_ix
    t_min = x[j_smooth]
    j_min = np.argmin(np.abs(t_avg - t_min))
    min_val= raw_fs[j_min]
    
    #Come up with narrowed fit range and guesses
    fit_rng = 40
    fit_ix = np.arange(j_min - fit_rng, j_min + fit_rng)
    fit_x = t_avg[fit_ix]
    fit_y = raw_fs[fit_ix]
    C_guess = (np.mean(fit_y[0:10]) + np.mean(fit_y[-11:-1]))/2 #avg continuum val at 2 endpoints
    A_guess = min_val - C_guess
    p0 = [t_min, .001, A_guess, 0, C_guess]
    
    popt, pcov = curve_fit(skew_L, fit_x, fit_y, p0)
    ax.plot(fit_x*1e3, skew_L(fit_x, *popt), 'k')

    
    #Visualizing:
    ax.plot(t_avg*1e3, raw_fs, '.', alpha = .2)
    ax.plot(x*1e3, fs, 'k', linewidth = .5, alpha = .8)
    
    ax.set_ylim((0, 4e-10))
    
    return popt

def vrs_from_L(raw_fs, ax):
    t_avg, max_fs = do_two_tone(raw_fs, ts[ix, :], n_split = 300, show_cutoff = False, ix_cutoff = 60)    
    popt_0 = fit_L(max_fs[:, 0], ax)    
    popt_1 = fit_L(max_fs[:, 1], ax)
    t_elapsed = (popt_0[0] + popt_1[0])/2 - crossing_emp
    vrs = t_elapsed*scan_rate_emp*2
    return vrs

def get_exc(vrs_gnd, vrs_exc):
    n_down = vrs_gnd**2
    n_up = vrs_exc**2
    return n_up/(n_up + n_down)
