#Standard imports
import numpy as np
import os, json, h5py, time
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
from scipy import signal

#Importing analysis code from data_analysis folder
import data_analysis.simple_clock as sc

from data_analysis.MM_analysis.ramsey import process_ramsey_data as ramsey
from data_analysis.cavity_clock.read_data import *
from data_analysis.cavity_clock.helpers import *
from pico.clients.cavity_clock_clients.params import *
from data_analysis.cavity_clock.cavity_sweep_min import *
from data_analysis.cavity_clock.cavity_sweep_Lorentzian import *
from data_analysis.cavity_clock.MM_plotter_package import *

from data_analysis.sr1_fit import processAxialTemp, fit, axialTemp


from data_analysis.clock_lock import iq_lib as iq


#CAVITY LISTENERS            

def filtered_cavity_time_domain(update, ax, seq):
    #MM 03222023 added listening for sweep params
    #print("sweep params: {}".format(sweep))
    #MM -03212023 written for compatibility with multiple triggers of ps6000a
    #MM05082023 determining window fits from sequence
    fixed_ixs = get_windows (seq) #MM 20230508 added in "MM plotter package"
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            ax.clear()
            fits, _ = process_shot_var(value, fixed_ixs, ax = ax)
            ax.legend(labelcolor = 'k')
            return True, fits, fixed_ixs
        else:
            return False, None, None
'''
def filtered_cavity_time_domain(update, ax, seq):
    #MM 03222023 added listening for sweep params
    #print("sweep params: {}".format(sweep))
    #MM -03212023 written for compatibility with multiple triggers of ps6000a
    #MM05082023 determining window fits from sequence
    windows = get_windows (seq) #MM 20230508 added in "MM plotter package"
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            ax.clear()
            fits, _ = process_shot_1ens(value, ax = ax)
            ax.legend(labelcolor = 'k')
            return True, fits, windows
        else:
            return False, None, None'''
            
def sweep_to_f(update, ax, ax2, data_x, data_y, datums, sweep, fixed_ixs):
    #MM 20230508 assuming run after filtered_cavity_time_domain w/ process_shot_var
    ax.set_facecolor('xkcd:pinkish grey')
    #Extracting shot number
    for message_type, message in update.items():
        value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            n, _ = get_shot_num(value, str_end = '.cavity_probe_pico.hdf5')
        else:
            n = None
    if n >1:
        #Setting numerical factors for converting sweep fitted times to cavity frequencies. 
        mod_rate = 1.5e6 #MHz/V on 11/2 demod synthesizer
        t_range = .04 #set assuming 40 ms windows
        v_range = sweep[1] - sweep[0]
        #v_fixed = sweep[2]
        conv = v_range/t_range * mod_rate
        #t_fixed = (v_fixed - sweep[0])*t_range/v_range 
    
        markers_fixed = ['.', '.', 'o', 'o']
        marker_swept = 'x'
        n_windows = len(fixed_ixs)
        dfs = np.zeros(n_windows)
        fixed_counter = 0
        last_swept = [i for i in np.arange(n_windows) if not fixed_ixs[i]][-1]
        for i in np.arange(n_windows):
            if not fixed_ixs[i]:
                dfs[i] = (datums[i, 0] - datums[last_swept, 0])*conv
                ax.plot(n, dfs[i], marker_swept, color = cs[i])
            else:
                dfs[i] = datums[i, 0] #just save voltages. 
                ax2.plot(n, dfs[i], markers_fixed[fixed_counter], color = cs[i], alpha = .1)
                fixed_counter +=1
        data_x.append(n)
        data_y.append(dfs)       
    
            
def exc_frac_cavity(update, ax, data_x, data_y, vrs_gnd, vrs_exc, x_ax):
    n_down = vrs_gnd**2
    n_up = vrs_exc**2
    exc_frac = n_up/(n_up + n_down)
    x_val = get_cav_axis(update, x_ax)
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
            
	
def atom_number(update, ax, data_x, data_y, bad_points = None, time_domain = False, time_name = 'sequencer.t_dark', freq_domain = True, add_fit= False):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('clock_pico')
        if message_type == 'record' and value is not None:
            gnd, exc, background, freq, _, shot_num, t_dark = get_clock_data(value, time_name = time_name)
            atom_num = np.sum((gnd + exc - 2*background)[pico_shot_range])
            num_gnd = np.sum((gnd -background)[pico_shot_range])
            num_exc = np.sum((exc -background)[pico_shot_range])
            
            if shot_num is None or shot_num < 2:
               return False
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
            	ax.set_xlabel('Frequency (-116.55 MHz)')
            	    
            else:
                x_ax = shot_num
                ax.set_xlabel('Shot number')
            data_x.append(x_ax)
            data_y.append(atom_num)
            if bad_points is not None:
                this_bad = atom_num < no_atoms_thresh
                bad_points.append(this_bad)
                if this_bad:
                    col = 'gray'
                else:
                    col = 'k'
            ax.plot(x_ax, num_gnd, 's', color = 'white', fillstyle='none', zorder=3)
            ax.plot(x_ax, num_exc, 'd', color = 'white', zorder=2)
            ax.plot(x_ax, atom_num, 'o', color = col, zorder=1)
            ax.set_ylabel('Total atom number')
            return True

def exc_frac(update, ax, data_x, data_y, time_domain = False, time_name = 'sequencer.clock_phase', freq_domain = True, add_fit= False, n_avg = 1, bad_shot= None):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('clock_pico')
        if message_type == 'record' and value is not None:
            gnd, exc, background, freq, _, shot_num, t_dark = get_clock_data(value, time_name = time_name)
            if bad_shot:
                col = 'gray'
            else:
                col = 'k'
            if shot_num is None or shot_num < 2:
                return False
            exc_frac = calc_excitation(np.sum((gnd - background)[pico_shot_range]), np.sum((exc - background)[pico_shot_range]))
            if time_domain:
               x_ax = t_dark
               ax.set_xlabel(time_name)
            elif freq_domain:
            	x_ax = (freq - freq_offset)
            	ax.set_xlabel('Frequency (-116.55 MHz)')            	    
            else:
                x_ax = shot_num
                ax.set_xlabel('Shot number')
            data_x.append(x_ax)
            data_y.append(exc_frac)

            if (n_avg > 1) and (len(data_y) > n_avg):
                binned_x, binned_data = do_moving_avg(data_x, data_y, n_avg)
                ax.clear()
                ax.plot(binned_x, binned_data, 'o', color = col)
                ax.set_xlabel('Shot number')
                
            else:
                ax.plot(x_ax, exc_frac, 'o', color = col)
            ax.set_ylabel('Excitation Fraction')
            return True
            

def get_clock_data(path, time_name = 'sequencer.t_dark'):
    shot_num, folder_path = get_shot_num(path)  
    f = h5py.File(path)
    gnd = np.array(f['gnd'])
    exc = np.array(f['exc'])
    background = np.array(f['bgd'])
    ts = np.array(f['time'])
    if shot_num is not None:
        f_name = "{}.conductor.json".format(shot_num)
        path = os.path.join(folder_path, f_name)
        f = open(path)
        c_json = json.load(f)
        freq = c_json['clock_sg380']
        try:
            t_dark = c_json[time_name]
        except:
            t_dark = None
            #print('dark time not specified')
    else:
        freq = None
        t_dark = None
    return gnd, exc, background, freq, ts, shot_num, t_dark  
               
def get_shot_num(path, str_end = None):
    if str_end is None:
        str_end = '.clock_pico.hdf5'
    head, tail = os.path.split(path)
    split_str = tail.partition(str_end)
    try:
        shot_num = int(split_str[0])
    except:
        shot_num = None
    return shot_num, head

def get_clock_paths(path):
    str_end = '.clock_pico.hdf5'
    head, tail = os.path.split(path)
    split_str = tail.partition(str_end)
    shot_num = int(split_str[0])
    path_last = os.path.join(head, str(shot_num - 1)+ str_end)
    return path_last, shot_num, head

def get_clock_data_old(path, time_name = 'sequencer.t_dark'):
    path_last, shot_num, folder_path= get_clock_paths(path)
    if shot_num > 0:
        f = h5py.File(path)
        f_last = h5py.File(path_last)
        gnd = np.array(f_last['exc'])
        exc = np.array(f_last['gnd'])#MM 080221 keeping up with ever- changing fun lol
        background = np.array(f['bgd'])
        ts = np.array(f['time'])
        
        f_name = "{}.conductor.json".format(shot_num)
        path = os.path.join(folder_path, f_name)
        f = open(path)
        c_json = json.load(f)
        freq = c_json['clock_sg380']
        try:
            t_dark = c_json[time_name]
        except:
            t_dark = None
            print('dark time not specified')
    return gnd, exc, background, freq, ts, shot_num, t_dark
#=======
#>>>>>>> 303bf0f26f8f897e7ed4995cff099dc2405b40ec
        
