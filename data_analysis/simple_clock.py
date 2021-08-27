from scipy import signal
from scipy.optimize import curve_fit
import numpy as np
import scipy as sc
from scipy.constants import *
from scipy.stats import chi2
from matplotlib import pyplot as plt
import allantools
import cv2
import os,sys,inspect
import json, h5py
from data_analysis.imaging_tools import process_file
from data_analysis.imaging_tools import process_file_return_background

#currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
#parentdir = os.path.dirname(currentdir)
#sys.path.insert(0,parentdir) 


# Note: Default atom number calibration 'calGain5' from 10/26/18 notebook: noise_characterization.ipynb
# This was calibrated using a PMT preamp gain of 5.  Changing 'pmtGain' will rescale the calibration appropriately

# Note: 'cutoff_A' and 'cutoff_B' are the atom number cuts in terms of calibrated atom number for the respective locks

# Note: 'runAtoms' is the number of atoms used during typical clock operation.  Useful for computing lever arm
# and density shift for run condition.

shot_offset = 3
pico_shot_range = np.arange(10, 25)
freq_offset = 116.1e6
peakfreq = 0
   
#Packaged 072721 MM

def load_freq(settings):
	modified_shot = settings['shot_number'] - shot_offset
	f_name = "{}.conductor.json".format(modified_shot)
	path = os.path.join(settings['data_path'], settings['exp_name'], f_name)
	f = open(path)
	c_json = json.load(f)
	return c_json['clock_sg380']
	
def calc_excitation(gnd, exc):
	frac = float(exc)/(exc + gnd)
	return frac

def add_trace(trace_exc, trace_gnd, trace_bgd, thisAx):
	thisAx.clear()
	thisAx.plot(trace_gnd, 'o', color = 'black')
	thisAx.plot(trace_bgd, 'o', color = 'gray')
	thisAx.plot(trace_exc, 'o', color = 'white' , alpha = .7)
	thisAx.fill_between(pico_shot_range,0, trace_gnd[pico_shot_range], alpha = .4, color = 'grey')
	thisAx.set_ylabel('PMT Voltage')
	thisAx.set_xlabel('Time traces')

def add_freq_domain(freq, exc, thisAx):
	thisAx.plot(freq-freq_offset, exc, 'o', color = 'black')
	thisAx.set_ylabel('Excitation Fraction')
	
	thisAx.set_xlabel('Frequency (-116.1 MHz)')
	
def add_shot_num(shot_num, exc, thisAx):
	thisAx.plot(shot_num, exc, 'o-', color = 'black')
	thisAx.set_xlabel('Shot Number')
	
def make_simple_plot(shot_num, trace_exc, trace_gnd, trace_bgd, freq, exc, ax):
	add_freq_domain(freq, exc, ax[0])
	add_shot_num(shot_num, exc, ax[1])
	ax[1].yaxis.tick_right()
	add_trace(trace_exc, trace_gnd, trace_bgd, ax[2])

	
def gaussian(x, mu, sig,a, b):
	return a*np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.))) + b    
  
def fit_gaussian(freqs, exc):
	cen_guess = np.argmax(exc)
	fit, cov = curve_fit(gaussian,freqs, exc, p0=[freqs[cen_guess], 30, exc[cen_guess], 0.01])
	FWHM = fit[1]*2*np.sqrt(2*np.log(2))
	return fit, cov, FWHM
	
def add_gaussian(freqs, exc, freq_ax, offset = True, inverted = False):
        if inverted:
            fit, cov, FWHM = fit_inverted_gaussian(freqs, exc)
        else:
            fit, cov, FWHM = fit_gaussian(freqs, exc)
        fit_x = np.linspace(fit[0] - 3*fit[1], fit[0] + 3*fit[1], 100)
        gauss = gaussian(fit_x, *fit)
        if offset:
            x_ax = fit_x - freq_offset
        else:
            x_ax = fit_x
        freq_ax.plot(x_ax, gauss, 'gray')
        freq_ax.set_title("Cen: {:.2f}. FWHM: {:.2f}".format(fit[0], FWHM), color = 'white')

def fit_inverted_gaussian(freqs, exc):
	cen_guess = np.argmin(exc)
	p0=[freqs[cen_guess], 10, exc[cen_guess] - 1, 1]
	fit, cov = curve_fit(gaussian,freqs, exc, p0 =p0)
	FWHM = fit[1]*2*np.sqrt(2*np.log(2))
	
	return fit, cov, FWHM
	
def import_pico_scan(data_path, exp_name, shot):
	path = os.path.join(data_path, exp_name, '{}.clock_pico.hdf5'.format(shot))
	path_last = os.path.join(data_path, exp_name, '{}.clock_pico.hdf5'.format(shot - 1))
	f = h5py.File(path)
	f_last = h5py.File(path_last)
	
	#Use this first config for old data (pre-072921)
	gnd = np.array(f_last['exc'])
	exc = np.array(f_last['bgd'])
	background = np.array(f['gnd'])
	
	#gnd = np.array(f_last['bgd'])
	#exc = np.array(f['gnd'])
	#background = np.array(f['exc'])
	
	#072921 MM permutation shifted by one when cavity probe + clock picos both running
	#gnd = np.array(f['gnd'])
	#exc = np.array(f['exc'])
	#background = np.array(f['bgd'])
	
	#Get frequency:
	f_name = "{}.conductor.json".format(shot)
	path = os.path.join(data_path, exp_name, f_name)
	f = open(path)
	c_json = json.load(f)
	freq = c_json['clock_sg380']
	
	return gnd, exc, background, freq


def simple_pico_clock(settings, fig, ax, data_x, data_y):
	shot = settings['shot_number'] - shot_offset
	if shot > 3:
		gnd, exc, background, freq = import_pico_scan(settings['data_path'], settings['exp_name'], shot)
		gnd_sub = gnd - background
		exc_sub = exc - background
		if settings['isCleanUp'] == False:
			frac = calc_excitation(np.sum(gnd_sub[pico_shot_range]), np.sum(exc_sub[pico_shot_range]))
		else :
			#swap if cleanup
			frac = calc_excitation(np.sum(exc_sub[pico_shot_range]), np.sum(gnd_sub[pico_shot_range]))
		print(freq)
		make_simple_plot(shot, exc, gnd, background, freq, frac, ax)
		fig.tight_layout()
		#Add data to live plotter dataset
		if data_x is None:
			data_x = []
		if data_y is None:
			data_y = []
		data_x.append(freq)
		data_y.append(frac)
		#Add curve if 3/4 of way through scan
		if shot == int(.75* settings['maxShots']):
			add_gaussian(data_x, data_y, ax[0])
			pass
		return fig, data_x, data_y	
	
	
	
#Note we haven't used cam clock in a good long while, but here's the old code in case that's useful as a stub:
def load_clock_images(settings):
#ROI = [300, 185, 75, 75]
	#cavity
	this_roi = [445, 565, 60, 120]
	#mot bucket
	#this_roi = [420, 220, 50, 60] 
#	default_name = "horizontal_mot_{}_horizontal_mot_fluor_vertical_mot_{}_fluorescence.png"
	default_name = "vertical_mot_{}_horizontal_mot_fluor_vertical_mot_{}_fluorescence.png"
	imgs = ['gnd', 'exc', 'background']
	modified_shot = settings['shot_number'] - shot_offset
	paths = [os.path.join(settings['data_path'], settings['exp_name'], default_name.format(img, modified_shot)) for img in imgs]
	gnd_sub = process_file(paths[0], ROI = this_roi, background = paths[2], zoom = True
	)
	gnd_raw = process_file(paths[0], ROI = this_roi, background = None, zoom = True
	)
	exc_sub = process_file(paths[1], ROI = this_roi, background = paths[2], zoom = True)
	return gnd_sub, exc_sub

def load_clock_images_bkgd(settings):
#ROI = [300, 185, 75, 75]
	default_name = "vertical_mot_{}_horizontal_mot_fluor_vertical_mot_{}_fluorescence.png"
	imgs = ['gnd', 'exc', 'background']
	modified_shot = settings['shot_number'] - shot_offset
	paths = [os.path.join(settings['data_path'], settings['exp_name'], default_name.format(img, modified_shot)) for img in imgs]
	bkgd = process_file_return_background(paths[2], ROI = [390, 190, 100, 75], background = paths[2], zoom = True
	)

	return bkgd


def simple_cam_clock(settings, fig, ax):
	gnd_sub, exc_sub = load_clock_images(settings)
	exc_frac = calc_excitation(np.sum(gnd_sub), np.sum(exc_sub))
	freq = load_freq(settings)
	print(freq)
	#print(settings)
	# Add J/data/date/notebooks/ to path    
	add_to_plot(settings, freq, exc_frac, fig, ax)
#	add_to_plot(freq, exc_frac, fig, ax)
	fig.tight_layout()
	return fig
