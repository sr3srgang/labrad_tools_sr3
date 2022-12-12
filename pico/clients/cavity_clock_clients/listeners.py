#Standard imports
import numpy as np
import os, json, h5py, time
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
from scipy import signal

#Importing analysis code from data_analysis folder
import data_analysis.simple_clock as sc
from data_analysis.pico import do_two_tone, do_single_tone
from data_analysis.MM_analysis.ramsey import process_ramsey_data as ramsey
from data_analysis.cavity_clock.read_data import *
from data_analysis.cavity_clock.helpers import *
from pico.clients.cavity_clock_clients.params import *
from data_analysis.cavity_clock.cavity_sweep_min import *
from data_analysis.cavity_clock.cavity_sweep_Lorentzian import *
from data_analysis.sr1_fit import processAxialTemp, fit, axialTemp

#MM 06102022 commented old zuko version in merge conflict with toph
'''
<<<<<<< HEAD
pico_shot_range = np.arange(10, 25)
freq_offset = 116.1e6
from scipy.signal import find_peaks
from sys import platform

crossing_emp = .00154
t_range_emp = [.007, .017]
scan_rate_emp = 1e6/(20e-3) #1MHz/20 ms
def get_cavity_data(abs_data_path, trace = 'gnd'):
    if platform == 'win32':
        abs_data_path = 'K:/' + path[15:]
    with h5py.File(abs_data_path) as h5f:
        data = np.array(h5f[trace])
        #self.test = np.array(h5f['test_new_trig'])
        #print(self.test)
        ts = np.array(h5f['time'])
    return data, ts
=======
'''
from data_analysis.clock_lock import iq_lib as iq

#>>>>>>> 303bf0f26f8f897e7ed4995cff099dc2405b40ec


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
    
def cavity_probe_two_tone(update, ax, trace = 'gnd', val = False, do_lorentzian = True):
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
            ax.set_ylim((0, 5e-10))
            
            #try to find vrs
            if do_lorentzian:
                vrs = vrs_from_L(data, ts, ax)
            else:
                vrs = get_vrs(t_avg, max_fs, ax)
            print("vrs: " + str(vrs*1e-6))
            return True, vrs
        else:
            return False, None
            
def Q_fit(tprime, A, delta, kappaprime,c):
    return (A * (tprime - delta)/(kappaprime/2)) / (1 + ((tprime-delta) /kappaprime/2)**2 ) + c
            
def process_homodyne(data, ts, t_a, t_b, do_filter = True):
    #written 041322 MM 
    ix_a = np.argmin(np.abs(ts - t_a))
    ix_b = np.argmin(np.abs(ts - t_b))
    
    data_range = data[ix_a:ix_b]
    ts_range = ts[ix_a:ix_b]
    freqs = np.linspace(0,(1.5e6/1)*0.5 , len(ts_range))
    
    if do_filter:
        #Filter from john's notebook
        fc = 4000
        #Design of digital filter requires cut-off frequency to be normalised by sampling_rate/2
        sampling_rate = 1/(ts_range[2]-ts_range[1])
        ncut = 200
        w = fc /(sampling_rate/2)
        b, a = signal.butter(3, w, 'low', analog = False)
        data_range = signal.filtfilt(b, a, data_range.ravel())[ncut:]
        ts_range = ts_range[ncut:]
        freqs = freqs[ncut:]
    
    return data_range, ts_range, freqs

def fit_cavity_freq(data, ts, t_a, t_b, ax = None, do_filter = False):
    output_V, ts_range, freqs = process_homodyne(data, ts, t_a, t_b, do_filter = do_filter)
    cav_1 = 260429.39915606365
    fit, cov = curve_fit(Q_fit, freqs, output_V, p0=[2e-2, cav_1+1e3, 3e4, 0], bounds = ((-np.inf, 2.3e5, 3e4, -np.inf),(np.inf, np.inf, 4.5e4, np.inf)))
    if ax is not None:
        #plot
        ax.plot(ts_range*1e3, Q_fit(freqs, *fit), color = 'white')
    
    return fit[1] #returns cavity detuning

def mean_v(data, ts, t_a, t_b, ax = None, do_filter = False):
    output_V, ts_range, freqs = process_homodyne(data, ts, t_a, t_b, do_filter = do_filter)
    mean_V = np.mean(output_V)
    if ax is not None:
        ax.plot(ts_range*1e3, np.ones(len(ts_range))*mean_V, color = 'grey')
    return np.mean(output_V)
    
def filtered_cavity_time_domain(update, ax, trace = 'gnd', val = False, do_fit = False, t_bounds = None, subtract_acc = True):
    #MM 051722 synchronous acc. subtraction option
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            data, ts = get_cavity_data(value, trace)
            data, ts, _ = process_homodyne(data, ts, ts[0], ts[-1]) #pre-filter
            ax.clear()
            in_range = ts*1e3 <100 #MM 11232022 hacking pico window shorter
            ax.plot(1e3*ts[in_range], data[in_range], '.k', ms = .5)
            if subtract_acc:
                time.sleep(.1)
                n, data_head = get_shot_num(value, str_end = '.cavity_probe_pico.hdf5')
                acc_data, acc_ts = get_cavity_data(os.path.join(data_head, '{}.accelerometer_pico.hdf5'.format(n)), trace)
                acc_data, acc_ts, _ = process_homodyne(acc_data, acc_ts, acc_ts[0], acc_ts[-1])
                assert(np.all(ts == acc_ts))
                data = data # turn off- acc_data #subtract off accelerometer data NOTE MIGHT NEED TO OPTIMIZE AMPLITUDE HERE
                ax.plot(ts*1e3, data, color = 'gray', alpha = .7, linewidth = 1)
            ax.set_xlabel('Cavity probe time (ms)')
            ax.set_ylabel('homodyne output')
            #ax.set_ylim((0, 5e-10))
            fit_fxns = [fit_cavity_freq, mean_v]
            if do_fit > 0: #some type of fit turned on
                datums = np.zeros(len(t_bounds))
                fxn = fit_fxns[do_fit - 1] #apply corresponding fit function
                for i in np.arange(len(t_bounds)):
                    datums[i] = fxn(data, ts, t_bounds[i][0], t_bounds[i][1], ax, do_filter = False) #don't re-filter
                return True, datums
            else:
                return True, None
        else:
            return False, None   
def correlations(update, ax, datums):
    ax.set_facecolor('xkcd:pinkish grey')
    ax.plot(datums[0] - datums[1], datums[0] - datums[2], 'ok')
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel('V0 - V1')
    ax.set_ylabel('V0 - V3')
    
def cavity_time_domain(update, ax, trace = 'gnd', val = False):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            data, ts = get_cavity_data(value, trace)
            n, _ = get_shot_num(value, str_end = '.cavity_probe_pico.hdf5')
            #t_avg, max_fs = do_single_tone(data, ts)
            ax.clear()
            ax.plot(ts*1e3, data, color = 'k')
            #ax.plot(t_avg*1e3, max_fs[:, 1], color = 'white')
            ax.set_xlabel('Cavity probe time (ms)')
            ax.set_ylabel('homodyne output')
            #ax.set_ylim((0, 5e-10))
            
            return True, None
        else:
            return False, None
            
def bare_cavity_single_tone(update, ax, trace = 'gnd', val = False, do_lorentzian = True):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            data, ts = get_cavity_data(value, trace)
            n, _ = get_shot_num(value, str_end = '.cavity_probe_pico.hdf5')
            t_avg, max_fs = do_single_tone(data, ts)
            ax.clear()
            ax.plot(t_avg*1e3, max_fs[:, 0], color = 'k')
            #ax.plot(t_avg*1e3, max_fs[:, 1], color = 'white')
            ax.set_xlabel('Cavity probe time (ms)')
            ax.set_ylabel('Power (arb)')
            #ax.set_ylim((0, 5e-10))
            return True, None
            '''
            #try to find vrs
            if do_lorentzian:
                vrs = vrs_from_L(data, ts, ax)
            else:
                vrs = get_vrs(t_avg, max_fs, ax)
            print("vrs: " + str(vrs*1e-6))
            return True, vrs
            '''
        else:
            return False, None            

def do_iq(update, ax, t_min, t_max, t_cut, rf_offset, rf_slope, trace = 'gnd', val = False, do_lorentzian = True):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            data, ts = get_cavity_data(value, trace)
            in_range = np.logical_and(ts > t_min, ts < t_max)
            omega_rf = 2*np.pi*(ts[in_range]*rf_slope + rf_offset)
            [V_c, V_s, t_arr, omega_rf] = iq.do_iq_fixed(ts[in_range], data[in_range], omega_rf)
            in_range = t_arr > t_cut
            ax.clear()
            ax.plot(V_c[in_range]*1e3, V_s[in_range]*1e3, color = 'k')
            #ax.plot(t_avg*1e3, max_fs[:, 1], color = 'white')
            ax.set_xlabel('I (mV)')
            ax.set_ylabel('Q (mV)')
            ax.set_xlim(-2, 2)
            ax.set_ylim(-2, 2)
            ax.set_aspect('equal', adjustable='box')
            #ax.set_ylim((0, 5e-10))
            return True, None
            '''
            #try to find vrs
            if do_lorentzian:
                vrs = vrs_from_L(data, ts, ax)
            else:
                vrs = get_vrs(t_avg, max_fs, ax)
            print("vrs: " + str(vrs*1e-6))
            return True, vrs
            '''
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
            
	
def atom_number(update, ax, data_x, data_y, bad_points = None, time_domain = False, time_name = 'sequencer.t_dark', freq_domain = True, add_fit= False):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('clock_pico')
        if message_type == 'record' and value is not None:
            gnd, exc, background, freq, _, shot_num, t_dark = get_clock_data(value, time_name = time_name)
            atom_num = np.sum((gnd + exc - 2*background)[pico_shot_range])
            if shot_num is None or shot_num < 1:
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
            ax.plot(x_ax, atom_num, 'o', color = col)
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
            if shot_num is None or shot_num < 1:
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
            








#<<<<<<< HEAD
'''            
tempZ, p0, p1, p2,p3, p4, nzBar = processAxialTemp((-1*np.array(freq_cut[0::1])+ np.mean(freq))/1e3, soln) # frequency input needs to be in kHz
    
print('Temperature in the lattice: '+str(np.round(tempZ, 2))+' uK')
print('Probability in the ground band: '+str(np.round(p0, 3)))
print('Probability in the 1st excited band: '+str(np.round(p1, 3)))
print('Probability in the 2nd excited band: '+str(np.round(p2, 3)))
print('Probability in the 3rd excited band: '+str(np.round(p3, 3)))
print('Probability in the 4th excited band: '+str(np.round(p4, 3)))

print('<n_z> = '+str(np.round(nzBar,3)))         
''' 
def get_clock_data(path, time_name = 'sequencer.t_dark'):
    #try:
    #    shot_num, folder_path = get_shot_num(path)
    #except:
        #modify_path_here
#    if platform == 'win32':
#        path = 'K:/' + path[15:]
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
            print('dark time not specified')
    else:
        freq = None
        t_dark = None
    return gnd, exc, background, freq, ts, shot_num, t_dark  
               
def get_shot_num(path):
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
        
