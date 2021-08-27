#Standard imports
import numpy as np
import os, json, h5py
from scipy.signal import find_peaks
from scipy.optimize import curve_fit

#Importing analysis code from data_analysis folder
import data_analysis.simple_clock as sc
from data_analysis.pico import do_two_tone
from data_analysis.MM_analysis.ramsey import process_ramsey_data as ramsey
from data_analysis.cavity_clock.read_data import *
from data_analysis.cavity_clock.cavity_sweep_min import *
from data_analysis.cavity_clock.helpers import *
from data_analysis.sr1_fit import processAxialTemp, fit, axialTemp 

from pico.clients.cavity_clock_clients.params import *

#CAVITY LISTENERS            
def cavity_probe_time_trace(update, ax):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            ax.clear()
            data, ts = get_cavity_data(value)
            ts *= 1e3 #convert to ms
            ax.plot(ts, data, 'o', color = 'k')
            ax.set_xlabel('Exposure time (ms)')
            return True
    
def cavity_probe_two_tone(update, ax, trace = 'gnd', val = False):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            data, ts = get_cavity_data(value, trace)
            t_avg, max_fs = do_two_tone(data, ts)
            ax.clear()
            ax.plot(t_avg*1e3, max_fs[:, 0], color = 'k')
            ax.plot(t_avg*1e3, max_fs[:, 1], color = 'white')
            ax.set_xlabel('Cavity probe time (ms)')
            ax.set_ylabel('Power (arb)')
            ax.set_ylim((0, 2e-9))
            try:
                vrs = get_vrs(t_avg, max_fs, ax)
                print("vrs: " + str(vrs*1e-6))
            except:
                print("No vrs found")
                vrs = None
            #print('returning')
            return True, vrs
        else:
            return False, None

def exc_frac_cavity(update, ax, data_x, data_y, vrs_gnd, vrs_exc, x_ax):
    n_down = vrs_gnd**2
    n_up = vrs_exc**2
    exc_frac = n_up/(n_up + n_down)
    x_val = get_cav_axis(update, x_ax)
    print(x_val)
    print("Exc_frac: " + str(exc_frac))
    ax.plot(x_val, exc_frac, 'ok')
    ax.set_facecolor('xkcd:pinkish grey')


#CLOCK LISTENERS                           	
def pmt_trace(update, ax):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('clock_pico')
        if message_type == 'record' and value is not None:
            gnd, exc, background, _, ts, __, ___ = get_clock_data(value)
            ts*=1e3 #Convert to ms
            ax.clear()
            ax.plot(ts, gnd, 'o', color = 'black')
            ax.plot(ts, background, 'o', color = 'gray')
            ax.plot(ts, exc, 'o', color = 'white', alpha = .6)
            ax.fill_between(ts[pico_shot_range],0, gnd[pico_shot_range], alpha = .4, color = 'grey')
            ax.set_xlabel('Exposure time (ms)')
            ax.set_ylabel('PMT Voltage')
            #ax.set_ylim((0, .2))
            #f = h5py.File(value)
            return True
            
	
def atom_number(update, ax, data_x, data_y, time_domain = False, time_name = 'sequencer.t_dark', freq_domain = True, add_fit= False):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('clock_pico')
        if message_type == 'record' and value is not None:
            gnd, exc, background, freq, _, shot_num, t_dark = get_clock_data(value, time_name = time_name)
            atom_num = np.sum((gnd + exc - 2*background)[pico_shot_range])
            if time_domain:
               x_ax = t_dark*1e3
               ax.set_xlabel(time_name +' (ms)')
            elif freq_domain:
            	x_ax = (freq - freq_offset)
            	if add_fit:
            	    if len(data_y) > 5:
            	        ax.clear()
            	        ax.plot(data_x, data_y, 'o', color = 'k')
            	        sc.add_gaussian(data_x, data_y, ax, offset = False)
            	    else:
            	        print('Too few points to fit')
            	ax.set_xlabel('Frequency (-116.1 MHz)')
            	    
            else:
                x_ax = shot_num
                ax.set_xlabel('Shot number')
            data_x.append(x_ax)
            data_y.append(atom_num)
            ax.plot(x_ax, atom_num, 'o', color = 'k')
            ax.set_ylabel('Total atom number')
            return True

def exc_frac(update, ax, data_x, data_y, time_domain = False, time_name = 'sequencer.clock_phase', freq_domain = True, add_fit= False, n_avg = 1):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('clock_pico')
        if message_type == 'record' and value is not None:
            gnd, exc, background, freq, _, shot_num, t_dark = get_clock_data(value, time_name = time_name)
            if shot_num is None or shot_num < 1:
                return False
            exc_frac = calc_excitation(np.sum((gnd - background)[pico_shot_range]), np.sum((exc - background)[pico_shot_range]))
            if time_domain:
               x_ax = t_dark
               ax.set_xlabel(time_name)
            elif freq_domain:
            	x_ax = (freq - freq_offset)
            	ax.set_xlabel('Frequency (-116.1 MHz)')            	    
            else:
                x_ax = shot_num
                ax.set_xlabel('Shot number')
            data_x.append(x_ax)
            data_y.append(exc_frac)

            if (n_avg > 1) and (len(data_y) > n_avg):
                binned_x, binned_data = do_moving_avg(data_x, data_y, n_avg)
                ax.clear()
                ax.plot(binned_x, binned_data, 'ok')
            else:
                ax.plot(x_ax, exc_frac, 'o', color = 'k')
            ax.set_ylabel('Excitation Fraction')
            return True
            





   




        
