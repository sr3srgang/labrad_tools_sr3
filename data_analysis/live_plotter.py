from scipy import signal
import numpy as np
import scipy as sc
from scipy.constants import *
from scipy.stats import chi2
from matplotlib import pyplot as plt
import allantools
import cv2
import os,sys,inspect
import json

import data_analysis.simple_clock as sc
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

shot_offset = 5
   
def load_clock_images(settings):
#ROI = [300, 185, 75, 75]
	this_roi = [445, 600, 60, 120]
#	default_name = "horizontal_mot_{}_horizontal_mot_fluor_{}_fluorescence.png"
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
	
def return_f_e_pico(settings, fig, ax):
	freq = sc.load_freq(settings)
	gnd, exc, background, freq = sc.import_pico_scan(settings['data_path'], settings['exp_name'], settings['shot_number'])
	gnd_sub = gnd - background
	exc_sub = exc - background
	frac = sc.calc_excitation(np.sum(gnd_sub[sc.pico_shot_range]), np.sum(exc_sub[sc.pico_shot_range]))
	return freq, frac
	
def add_to_plot(settings, freq, exc, fig, ax):
	fig.set_size_inches(12, 6)
	ax[0].plot(freq, exc, 'o', color = 'black')
	ax[0].set_ylabel('y-axis')
	ax[0].set_xlabel('Frequency')
	ax[0].set_title('Excitation Fraction')
	#ax[0].set_ylim([-0.01,np.max(exc)])
	
	ax[1].plot(settings['shot_number'], exc, 'o', color = 'black')
	ax[1].set_ylabel('y-axis')
	ax[1].set_xlabel('Shot Number')
	ax[1].set_title('Excitation Fraction')
	print(exc)

	
def rfe(settings, fig, ax):
	gnd_sub, exc_sub = load_clock_images(settings)
	exc_frac = calc_excitation(np.sum(gnd_sub), np.sum(exc_sub))
	freq = load_freq(settings)
	#print(freq)
	#print(settings)
	# Add J/data/date/notebooks/ to path    
	#add_to_plot(freq, exc_frac, fig, ax)
	#fig.tight_layout()
    
	return freq, exc_frac
	
def return_ground_counts(settings, fig, ax):
	gnd_sub, exc_sub = load_clock_images(settings)
	#exc_frac = calc_excitation(np.sum(gnd_sub), np.sum(exc_sub))
	#freq = load_freq(settings)
	#print(freq)
	#print(settings)
	# Add J/data/date/notebooks/ to path    
	#add_to_plot(freq, exc_frac, fig, ax)
	#fig.tight_layout()
    
	return np.sum(gnd_sub)
	
def return_bkgd(settings, fig, ax):
	bkgd = load_clock_images_bkgd(settings)
	bkgd_sum = np.sum(bkgd)
	#exc_frac = calc_excitation(np.sum(gnd_sub), np.sum(exc_sub))
	#freq = load_freq(settings)
	#print(freq)
	#print(settings)
	# Add J/data/date/notebooks/ to path    
	#add_to_plot(freq, exc_frac, fig, ax)
	#fig.tight_layout()
    
	return bkgd_sum
	
def plot_test(settings, fig, ax):
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
