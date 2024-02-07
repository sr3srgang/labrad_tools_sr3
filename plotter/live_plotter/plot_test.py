from scipy import signal
import numpy as np
import scipy as sc
from scipy.constants import *
from scipy.stats import chi2
from matplotlib import pyplot as plt

import allantools

import os,sys,inspect
#currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
#parentdir = os.path.dirname(currentdir)
#sys.path.insert(0,parentdir) 


# Note: Default atom number calibration 'calGain5' from 10/26/18 notebook: noise_characterization.ipynb
# This was calibrated using a PMT preamp gain of 5.  Changing 'pmtGain' will rescale the calibration appropriately

# Note: 'cutoff_A' and 'cutoff_B' are the atom number cuts in terms of calibrated atom number for the respective locks

# Note: 'runAtoms' is the number of atoms used during typical clock operation.  Useful for computing lever arm
# and density shift for run condition.

def _plot_test():


    #print(len(good_indicies))
    #Dedrift data for PSDs and allan deviations 
    #Must use the cut timestamps to get the correct linear trend
    
    x1 = np.linspace(1, 10, 100)
    y1 = np.linspace(2, 20, 100)
    
    fig, ax = plt.subplots(1, 1)
    fig.set_size_inches(8, 6)
    
    ax.set_ylabel('y-axis')
    ax.set_xlabel('x-axis')
    ax.set_title('LIVE PLOTTER WORKING')
    ax.plot(x1, y1)
    
    
    return fig, ax

    
def plot_test(settings):
    import os
    import sys
    # Add J/data/date/notebooks/ to path    
    


    fig,ax = _plot_test()
    fig.tight_layout()
    
    return fig
