#GENERAL HELPERS
import numpy as np

def calc_excitation(gnd, exc):
	frac = float(exc)/(exc + gnd)
	return frac

def do_moving_avg(data_x, data_y, n):
        n_bins = len(data_y) - (n - 1)
        binned_data = np.zeros(n_bins)
        binned_x = data_x[0:n_bins]
        for i in np.arange(n_bins):
            binned_data[i] = np.mean(data_y[i:i+n])
        return binned_x, binned_data  

