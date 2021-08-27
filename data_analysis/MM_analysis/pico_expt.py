import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from scipy.optimize import curve_fit
import statsmodels.api as sm
import os, json, h5py
    
def calc_excitation(gnd, exc):
	frac = (exc.astype(np.float))/(exc + gnd)
	return frac 
	   
def import_pico_scan(data_path, exp_name, shot, keywords = ['clock_sg380']):
	path = os.path.join(data_path, exp_name, '{}.clock_pico.hdf5'.format(shot))
	path_last = os.path.join(data_path, exp_name, '{}.clock_pico.hdf5'.format(shot - 1))
	f = h5py.File(path)
	f_last = h5py.File(path_last)
	
	'''
	#Use this first config for old data (pre-072921)
	gnd = np.array(f_last['exc'])
	exc = np.array(f_last['bgd'])
	background = np.array(f['gnd'])
	
	#gnd = np.array(f_last['bgd'])
	#exc = np.array(f['gnd'])
	#background = np.array(f['exc'])
	'''
	#072921 MM permutation shifted by one when cavity probe + clock picos both running
	gnd = np.array(f['gnd'])
	exc = np.array(f['exc'])
	background = np.array(f['bgd'])
	
	#Get frequency:
	f_name = "{}.conductor.json".format(shot)
	path = os.path.join(data_path, exp_name, f_name)
	f = open(path)
	c_json = json.load(f)
	keys = np.zeros(len(keywords))
	for i in np.arange(len(keywords)):
	    keys[i] = c_json[keywords[i]]
	
	return gnd, exc, background, keys
  
def calc_exc_from_pops(pops):
    gnd_sub = pops[0] - pops[2]
    exc_sub = pops[1] - pops[2]
    exc_fracs = calc_excitation(gnd_sub, exc_sub)
    return exc_fracs
    
def pico_expt(data_path, exp_name, shots, ixs, keywords):
    n = len(shots)
    pops = np.zeros((n, 3))
    keys = np.zeros((n, len(keywords)))
    exc_fracs = np.zeros(n)
    for i in np.arange(n):
        gnd, exc, background, key_vals = import_pico_scan(data_path, exp_name, shots[i], keywords)
        pops[i, 0] = np.sum(gnd[ixs])
        pops[i, 1] = np.sum(exc[ixs])
        pops[i, 2] = np.sum(background[ixs])
        keys[i, :] = key_vals
        exc_fracs[i] = calc_exc_from_pops(pops[i, :])
    return pops, exc_fracs, keys
        
    
    

