from data_analysis.MM_analysis.ramsey import process_ramsey_data as ramsey
import numpy as np
import matplotlib.pyplot as plt
import data_analysis.simple_clock as sc
from scipy.optimize import curve_fit
from scipy.signal import find_peaks

#DIFFERENT FITTING ROUTINES            
def do_gaussian_fit(ax, data_x, data_y):
    if len(data_y) > 5:
        ax.clear()
        ax.plot(data_x, data_y, 'o', color = 'k')
        sc.add_gaussian(data_x, data_y, ax, offset = False)
    else:
        print("Too few points to fit")

def do_inverted_gaussian_fit(ax, data_x, data_y):
    if len(data_y) > 5:
        ax.clear()
        ax.plot(data_x, data_y, 'o', color = 'k')
        sc.add_gaussian(data_x, data_y, ax, offset = False, inverted = True)
    else:
        print("Too few points to fit")
 
def do_phase_fit(ax, data_x, data_y):
    if len(data_y) > 5:
        ax.clear()
        ax.plot(data_x, data_y, 'o', color = 'k')
        ramsey(data_y, data_x, p0 = [1, 2*np.pi, 0, 0], ax = ax)
    else:
        print("Too few points to fit")
        
def extrema(x, x0, a, b):
    return (x - x0)**2 * a + b
    
def do_local_max(ax, data_x, data_y):
    if len(data_y) > 5:
        peaks, _ = find_peaks(data_y, distance = len(data_y))
        ix = peaks[0]
        n_points = 5
        fit_ixs = np.arange(int(max(0, ix - n_points)), int(min(len(data_x), ix + n_points + 1)))
        popt, pcov = curve_fit(extrema, np.array(data_x)[fit_ixs], np.array(data_y)[fit_ixs], p0 = [data_x[ix], 0, data_y[ix]])
    
        show_x = np.linspace(data_x[min(fit_ixs)], data_x[max(fit_ixs)], 50)
        ax.clear()
        ax.plot(data_x, data_y, 'ok')
        ax.plot(show_x, extrema(show_x, *popt), color = 'gray')
        print(np.sqrt(np.diag(pcov)[0]))
        ax.set_title("Max: {:.2e}".format(popt[0]))

def do_local_min(ax, data_x, data_y):
    if len(data_y) > 5:
        peaks, _ = find_peaks(-np.array(data_y), distance = len(data_y))
        ix = peaks[0]
        n_points = 5
        
        fit_ixs = np.arange(int(max(0, ix - n_points)), int(min(len(data_x), ix + n_points + 1)))
        popt, pcov = curve_fit(extrema, np.array(data_x)[fit_ixs], np.array(data_y)[fit_ixs], p0 = [data_x[ix], 0, data_y[ix]])
    
        show_x = np.linspace(data_x[min(fit_ixs)], data_x[max(fit_ixs)], 50)
    
        ax.clear()
        ax.plot(data_x, data_y, 'ok')
        ax.plot(show_x, extrema(show_x, *popt), color = 'gray')
        print(np.sqrt(np.diag(pcov)[0]))
        ax.set_title("Min: {:.2e}".format(popt[0]))  
