import os
import numpy as np
import json, h5py
from data_analysis.pico import do_two_tone
import data_analysis.simple_clock as sc
from data_analysis.sr1_fit import processAxialTemp, fit, axialTemp 
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
   
def get_res_dips(t_avg, max_fs, t_range):
   in_range = (t_avg > t_range[0]) & (t_avg < t_range[1])
   n_points = len(t_avg[in_range])
   ix_0, _ = find_peaks(-max_fs[in_range, 0], distance = n_points)
   ix_1, _ = find_peaks(-max_fs[in_range, 1], distance = n_points)
   print('found peaks:')
   print(t_avg[in_range][ix_0], t_avg[in_range][ix_1])
   return t_avg[in_range][ix_0], t_avg[in_range][ix_1]
    
def get_vrs(t_avg, max_fs, t_range = t_range_emp, scan_rate = scan_rate_emp, t_cross = crossing_emp):
    t0, t1 = get_res_dips(t_avg, max_fs, t_range = t_range)
    t_elapsed = (t0 + t1)/2 - t_cross
    return t_elapsed*scan_rate*2
    
def cavity_probe_two_tone(update, ax, trace = 'gnd'):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            ax.clear()
            data, ts = get_cavity_data(value, trace)
            t_avg, max_fs = do_two_tone(data, ts)
            ax.plot(t_avg*1e3, max_fs[:, 0], color = 'k')
            ax.plot(t_avg*1e3, max_fs[:, 1], color = 'white')
            ax.set_xlabel('Cavity probe time (ms)')
            ax.set_ylabel('Het. tone power (arb)')
            try:
                vrs = get_vrs(t_avg, max_fs)
                print("vrs: " + str(vrs*1e-6))
            except:
                print("No vrs found")
            return True

#CLOCK LISTENERS
def get_expt(update):
    for message_type, message in update.items():
        value = message.get('clock_pico')
        if message_type == 'record' and value is not None:
            head, _ = os.path.split(value)
            _, expt = os.path.split(head)
            return expt

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
            #f = h5py.File(value)
            return True
            
def calc_excitation(gnd, exc):
	frac = float(exc)/(exc + gnd)
	return frac
	
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

def do_gaussian_fit(ax, data_x, data_y):
    if len(data_y) > 5:
        ax.clear()
        ax.plot(data_x, data_y, 'o', color = 'k')
        sc.add_gaussian(data_x, data_y, ax, offset = False)
    else:
        print("Too few points to fit")
            
def exc_frac(update, ax, data_x, data_y, time_domain = False, time_name = 'sequencer.t_pi', freq_domain = True, add_fit= False):
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
            	'''
            	if add_fit:
            	    if len(data_y) > 5:
            	        ax.clear()
            	        ax.plot(data_x, data_y, 'o', color = 'k')
            	        sc.add_gaussian(data_x, data_y, ax, offset = False)
            	    else:
            	        print('Too few points to fit')
            	 '''
            	ax.set_xlabel('Frequency (-116.1 MHz)')
            	    
            else:
                x_ax = shot_num
                ax.set_xlabel('Shot number')
            data_x.append(x_ax)
            data_y.append(exc_frac)
            ax.plot(x_ax, exc_frac, 'o', color = 'k')
            ax.set_ylabel('Excitation Fraction')
            return True

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
    if platform == 'win32':
        path = 'K:/' + path[15:]
    shot_num, folder_path = get_shot_num(path)

        
    f = h5py.File(path)
    gnd = np.array(f['gnd'])
    exc = np.array(f['bgd'])
    background = np.array(f['exc'])
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
        
