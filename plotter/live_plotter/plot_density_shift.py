from scipy import signal
import numpy as np
import scipy as sc
from scipy.constants import *
from scipy.stats import chi2
from matplotlib import pyplot as plt

import allantools

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 


import data_tools.process_8pt_lock
reload(data_tools.process_8pt_lock)
from data_tools.process_8pt_lock import *

import data_tools.process_BBR
reload(data_tools.process_BBR)
from data_tools.process_BBR import *

# Note: Default atom number calibration 'calGain5' from 10/26/18 notebook: noise_characterization.ipynb
# This was calibrated using a PMT preamp gain of 5.  Changing 'pmtGain' will rescale the calibration appropriately

# Note: 'cutoff_A' and 'cutoff_B' are the atom number cuts in terms of calibrated atom number for the respective locks

# Note: 'runAtoms' is the number of atoms used during typical clock operation.  Useful for computing lever arm
# and density shift for run condition.

fSr = 429.22800422987365e12

def adev_errs(taus, devs, data_length, T_cyc):
    eff_dof = ((3*(T_cyc*data_length-1)/(2*taus) - 2*(T_cyc*data_length-2)/(T_cyc*data_length)
     *(4*taus**2 / (4*taus**2 + 5))
    )) # formula for white frequency noise
    
    # the observed deviation is one sample from a distribution, so errors are from chi-sq. distribution
    err_low = (np.sqrt(eff_dof/chi2.ppf(0.84, eff_dof)*np.array(devs)**2))
    err_high = (np.sqrt(eff_dof/chi2.ppf(0.16, eff_dof)*np.array(devs)**2))
    
    return err_low, err_high

def common_dedrift(data_array, timestamp, data_array2, timestamp2):
    fit = np.polyfit(np.array(timestamp).astype(float),
                    np.array(data_array).astype(float), 1)
    drift = np.poly1d(fit)

    #Convert to 1542 nm
    comb_698 = 1716882.
    comb_1542 = 777577.
    lin_drift = -1.0*drift[1]/1e-6*comb_1542/comb_698
    
    return (data_array - drift(timestamp)), (data_array2-drift(timestamp2)), lin_drift, drift(timestamp)

def _process_density_shift(data,
                         cycle_time=None,
                         cutoff_A = 10,
                         cutoff_B = 10,
                         cuts = [(0,None)],
                         calGain1 = 0.0111,
                         pmtGain = 1.0,
                         runAtoms = 5.,
                         zeeman2_coeff = -2.456e-7, 
                         binsize = 50,
                         point_by_point = False,
                         use_bbr = False,
                         temp_file_date = 59327): 

    #Apply standard data processing for 8pt lock
    data = process_8pt_lock(data,cycle_time,cutoff_A,cutoff_B,cuts,calGain1,pmtGain)

    # Define some data variables for convenience
    totsA = data['8pt']['mean_atoms_a']
    totsB = data['8pt']['mean_atoms_b']
    atomsA = data['8pt']['tots']['meana']
    atomsB = data['8pt']['tots']['meanb']
    freqs = data['8pt']['freqs']
    great_indicies = data['8pt']['indicies']
    timestamps = data['8pt']['timestamps']-data['8pt']['timestamps'][0]
    cycle_time = data['8pt']['cycle_time']
    errs_Hz = data['8pt']['errs_Hz']
    
    #Compute BBR corrections if we want to do point-by-point
    temp_file1  = '/media/z/Sr1Software/temp_control_v3/Logging/Keithley1/'+str(temp_file_date)
    temp_file2  = '/media/z/Sr1Software/temp_control_v3/Logging/Keithley2/'+str(temp_file_date)
    if use_bbr == True:
        # commented out for now since we don't have a thermal model yet
        #data = process_bbr(data, temp_file1=bbr_file1, temp_file2=bbr_file2, verbose = False)
        #static = data['bbr_shift']['shifts']['static_shift']
        #dynamic = data['bbr_shift']['shifts']['dynamic_shift']
        static = BBR_static(21.0 + 273.15)/fSr
        dynamic = BBR_dynamic(21.0 + 273.15)/fSr
    else:
        static = BBR_static(23.5 + 273.15)/fSr
        dynamic = BBR_dynamic(23.5 + 273.15)/fSr
        pass    
        
    #Compute the lever arm for the density shift evaluation
    lever_arm = np.abs(totsA-totsB)/runAtoms
    
    shifts = {}
    #Common dedrift for shift calculations
    if great_indicies:
        A_common_dedrift, B_common_dedrift, lin_rate_common, trend_common = common_dedrift(freqs['meana'],timestamps,freqs['meanb'],timestamps+cycle_time/4.0)
    else:
        A_common_dedrift = []
        B_common_dedrift = []

    meanShift = np.mean(A_common_dedrift + errs_Hz['meana'] - B_common_dedrift - errs_Hz['meanb'])/fSr
    print("Raw shift between locks: "+str(np.round(meanShift,20)))
    
    #Compute the conditional shift in the center frequency
    shifts['center_shift'] = (A_common_dedrift + errs_Hz['meana'] - B_common_dedrift - errs_Hz['meanb'])/fSr

    #Systematic shifts.  Always computed in fractional frequency units
    #Compute 2nd order zeeman corrections (for point-by-point corrections)
    shifts['zeeman2a'] = zeeman2_coeff*(freqs['diffa']*2)**2/fSr
    shifts['zeeman2b'] = zeeman2_coeff*(freqs['diffb']*2)**2/fSr

    #Compute the average shift in f_center between the two lock conditions (from cut data)
    #Normalize by the difference in atom number for each measurement
    #This allows us to account for drifting atom number 
    # mean_no_drift_A + errs_Hz['meana'] - mean_no_drift_B - errs_Hz['meanb']
    if point_by_point == True: #Apply 2nd order zeeman corrections
        conditionalShift = np.mean( (shifts['center_shift']*fSr - shifts['zeeman2a']*fSr + shifts['zeeman2b']*fSr)/(atomsA-atomsB) )/fSr
    else:
        conditionalShift = np.mean(shifts['center_shift']/(atomsA-atomsB))

    #Compute the point-by-point shift in f_center between the two conditions
    #Normalize by the difference in atom number for each measurement
    #This allows us to account for drifting atom number 
    if point_by_point == True:
        shifts['pbp_center_shift'] = (shifts['center_shift']*fSr - shifts['zeeman2a']*fSr + shifts['zeeman2b']*fSr)/(atomsA-atomsB)/fSr
    else:    
        shifts['pbp_center_shift'] = (shifts['center_shift'])/(atomsA-atomsB)

    #Compute the average density shift for normal clock operation
    densityShift = np.mean(shifts['center_shift']*runAtoms/(atomsA-atomsB))
    
    #Compute the point-by-point density shift for atom number = runAtoms
    shifts['density_shift'] = shifts['center_shift']*runAtoms/(atomsA-atomsB)
    
    #Add in point-by-point corrections for the second order zeeman shift, density shift, and BBR shift
    #This point-by-point corrected frequency record can be used for analyzing the self-comparison stability
    #or the Si cavity frequency relative to fSr BIPM
    pbp = {}
    if use_bbr == True:
        pbp['meana'] = freqs['meana'] - atomsA*densityShift/runAtoms*fSr - shifts['zeeman2a']*fSr - (dynamic + static)*fSr
        pbp['meanb'] = freqs['meanb'] - atomsB*densityShift/runAtoms*fSr - shifts['zeeman2b']*fSr - (dynamic + static)*fSr
    else:
        pbp['meana'] = freqs['meana'] - atomsA*densityShift/runAtoms*fSr - shifts['zeeman2a']*fSr 
        pbp['meanb'] = freqs['meanb'] - atomsB*densityShift/runAtoms*fSr - shifts['zeeman2b']*fSr


    #Bin the data for gaussian/chi-squared analysis
    nBins = np.round(len(shifts['density_shift'])/binsize) #Compute number of bins
    
    #compute the mean and standard deviation of the density shift for each bin
    #Use these to compute chisquared value for the density shift evaluation
    #BUG FIX: Only compute these if we have sufficient data
    if len(shifts['density_shift']) > 2*binsize:    
        shifts['density_bin_means'] = np.array( [ np.mean(shifts['density_shift'][ii*binsize:(ii+1)*binsize]) for ii in range(nBins) ] )
        shifts['density_bin_stds'] = np.array( [np.std(shifts['density_shift'][ii*binsize:(ii+1)*binsize])/np.sqrt(binsize) for ii in range(nBins) ] )
        shifts['bin_index'] = np.array( [ np.mean(great_indicies[ii*binsize:(ii+1)*binsize]) for ii in range(nBins) ] )
        shifts['density_chisquared'] = chisquared(shifts['density_bin_means'],shifts['density_bin_stds'])
    else:
        print "Not enough data to compute binned chi-squared value"

    processed_data = {
        'binsize' : binsize,
        'freqs_pbp': pbp,
        'shifts': shifts,
        'mean_density_shift': densityShift,
        #'mean_conditional_shift': conditionalShift,
        'lever_arm':lever_arm,
        'runAtoms':runAtoms,
        'use_bbr':use_bbr,}
    
    data['density_shift'] = processed_data
    # hacks for now that we are not using the process_bbr routine with the thermal model
    bbr_shifts = {
        'shifts': {
        'static_shift' : static,
        'dynamic_shift': dynamic}}
    data['bbr_shift'] =  bbr_shifts
    
    return data


def _plot_density_shift(data, 
                        center_freq,
                        stability_1sec = 9.5e-17, 
                        taus='octave',
                        point_by_point=True, #Plot the stabilities w point-by-point corrections
                        plot_diff = False, #Plot the timeseries of the difference between the two locks
                        fitstart=20):
    colors = {
        'meana': 'r',
        'diffa': 'k',
        'meanb': 'darkviolet',
        'diffb': 'darkgrey',
        'rawa' : 'silver',
        'rawb' : 'gold',
        '-9/2a': 'b',
        '+9/2a': 'g', 
        '-9/2b': 'm',
        '+9/2b': 'y',
        'stab': 'navy',
        'err': 'salmon',
        'dens': 'aqua'
        }

    binsize = data['density_shift']['binsize']
    fracs = data['8pt']['fracs']
    fracs_raw = data['8pt']['all_fracs']
    tots = data['8pt']['tots']
    tots_raw = data['8pt']['all_tots']
    dither_points = data['8pt']['dither_points']
    pid_points = data['8pt']['pid_points']    
    freqs = data['8pt']['freqs']
    freqs_pbp = data['density_shift']['freqs_pbp']
    shifts = data['density_shift']['shifts']
    freqs_raw = data['8pt']['all_freqs']
    errs = data['8pt']['errs']
    errs_raw = data['8pt']['all_errs']
    errs_Hz = data['8pt']['errs_Hz']
    cycle_time = data['8pt']['cycle_time']
    timestamps = data['8pt']['timestamps']
    good_indicies = data['8pt']['indicies']
    totsA = data['8pt']['mean_atoms_a']
    totsB = data['8pt']['mean_atoms_b']
    atomsA = data['8pt']['tots']['meana']
    atomsB = data['8pt']['tots']['meanb']
    lever_arm = data['density_shift']['lever_arm']
    density_shift = data['density_shift']['mean_density_shift']
    runAtoms = data['density_shift']['runAtoms']
    use_bbr = data['density_shift']['use_bbr']
    if use_bbr == True:
        static = data['bbr_shift']['shifts']['static_shift']
        dynamic = data['bbr_shift']['shifts']['dynamic_shift']

    #print(len(good_indicies))
    #Dedrift data for PSDs and allan deviations 
    #Must use the cut timestamps to get the correct linear trend
    
    if good_indicies: #only perform this step if there's uncut data
        if point_by_point==True:
            mean_no_drift_A, lin_rate_A, drift_trend_A = dedrift_by_timestamp(freqs_pbp['meana'],timestamps)
            #needed to get raw frequency timeseries to overlap with drift fit
            if use_bbr == True:
                offset_a = np.mean( (atomsA*shifts['center_shift']+shifts['zeeman2a']) + static + dynamic )*fSr
            else:
                offset_a = np.mean( (atomsA*shifts['center_shift']+shifts['zeeman2a']) )*fSr
            mean_no_drift_B, lin_rate_B, drift_trend_B = dedrift_by_timestamp(freqs_pbp['meanb'],timestamps)
        else:
            mean_no_drift_A, lin_rate_A, drift_trend_A = dedrift_by_timestamp(freqs['meana'],timestamps)
            offset_a = 0.0
            mean_no_drift_B, lin_rate_B, drift_trend_B = dedrift_by_timestamp(freqs['meanb'],timestamps)

    fig, ax = plt.subplots(3, 3)
    fig.set_size_inches(18, 12)
    
    for ax_ in ax.flatten():
        ax_.grid(True, which='both')    
    
    """ subplot 0,0 and 0,1 excitation fractions and atom numbers"""
    #Use raw data so we can see glitches
    for dither_name, dither_fracs in fracs_raw.items():
        ax[0,0].plot(dither_fracs, '.', color='silver')
    if good_indicies:  #only perform this step if there's uncut data
        for dither_name, dither_fracs in fracs_raw.items():
            ax[0,0].plot(good_indicies, dither_fracs[good_indicies], '.', color=colors[dither_name[0]])
        
    for dither_name, dither_tots in tots_raw.items():    
        ax[0,1].plot(dither_tots, '.', color='silver')
    if good_indicies:  #only perform this step if there's uncut data
        for dither_name, dither_tots in tots_raw.items():    
            ax[0,1].plot(good_indicies, dither_tots[good_indicies], '.', color=colors[dither_name[0]])
        
    ax[0,0].set_ylabel('Excitation Fraction')
    ax[0,0].set_xlabel('Experiment Index')
    ax[0,0].set_ylim([-0.05, 1.05])
    ax[0,1].set_ylabel('Atom Number')
    ax[0,1].set_xlabel('Experiment Index')
    
        
    """ subplot 1,0 frequencies"""
    #Plot both raw and cut data
    offset = 0.0
    ax[1,0].plot(freqs_raw['meana']-center_freq, color=colors['rawa'])
    if good_indicies:  #only perform this step if there's uncut data
        ax[1,0].plot(good_indicies,freqs['meana']-center_freq, color=colors['meana'],linestyle='',marker='.')
    
    ax[1,0].plot(freqs_raw['meanb'] + offset - center_freq, color=colors['rawb'])
    if good_indicies:  #only perform this step if there's uncut data
        ax[1,0].plot(good_indicies,-1.0*center_freq + freqs['meanb'] + offset, color=colors['meanb'],linestyle='',marker='.')

        ax[1,0].plot(good_indicies, -1.0*center_freq + drift_trend_A + offset_a, '-.k', linewidth=2)


    ax[1,0].set_ylabel('Frequency [Hz]')
    ax[1,0].set_xlabel('Cycle Index')
    if good_indicies: #only perform this step if there's uncut data
        ax[1,0].legend(['%3.2f uHz/s @1542'%(lin_rate_A)],fontsize=14 )
    
    
    """ subplot 1,1 control allan """
    #Plot adevs for laser and field noise    
    if taus and good_indicies:
        # NOTE: the control signal for f_center is cancelling the long term laser noise.  Therefore it has the opposite sign!
        # in other words: Ctrl + laser = error ->  laser noise = error_signal - ctrl_signal
        (taus_, devs_, errs_, n) = allantools.oadev(signal.detrend(-1.0*mean_no_drift_A - errs_Hz['meana']) / 429e12,
            rate=1. / (cycle_time), data_type='freq', taus=taus)
        i = np.argwhere(taus_ < max(taus_) / 1)
        for tau, dev, err in zip(taus_[i], devs_[i], errs_[i]):
            err_l, err_h = adev_errs(tau, dev, data_length=len(mean_no_drift_A), T_cyc=cycle_time) #compute error bars
            ax[1,1].plot(tau, dev, 'o' , color=colors['meana'], label='laser A')
            ax[1,1].plot([tau, tau], [err_l, err_h], '-',color=colors['meana'])    
        (taus_, devs_, errs_, n) = allantools.oadev(signal.detrend(-1.0*mean_no_drift_B - errs_Hz['meanb']) / 429e12,
            rate=1. / (cycle_time), data_type='freq', taus=taus)
        i = np.argwhere(taus_ < max(taus_) / 1)
        for tau, dev, err in zip(taus_[i], devs_[i], errs_[i]):
            err_l, err_h = adev_errs(tau, dev, data_length=len(mean_no_drift_B), T_cyc=cycle_time) #compute error bars
            ax[1,1].plot(tau, dev, 'o' , color=colors['meanb'], label='laser B')
            ax[1,1].plot([tau, tau], [err_l, err_h], '-',color=colors['meanb'])   
    
        #The f_delta loop simply follows the magnetic field noise.  The control signal and the field have the same sign. 
        (taus_, devs_, errs_, n) = allantools.oadev((signal.detrend(freqs['diffa'],type='constant')+errs_Hz['diffa']) / 429e12,
            rate=1. / (cycle_time), data_type='freq', taus=taus)    
        i = np.argwhere(taus_ < max(taus_) / 1)
        for tau, dev, err in zip(taus_[i], devs_[i], errs_[i]):
            err_l, err_h = adev_errs(tau, dev, data_length=len(signal.detrend(freqs['diffa'],type='constant') / 429e12), T_cyc=cycle_time) #compute error bars
            ax[1,1].plot(tau, dev, 'o' , color=colors['diffa'], label='zeeman A')
            ax[1,1].plot([tau, tau], [err_l, err_h], '-',color=colors['diffa'])
        (taus_, devs_, errs_, n) = allantools.oadev((signal.detrend(freqs['diffb'],type='constant')+errs_Hz['diffb']) / 429e12,
            rate=1. / (cycle_time), data_type='freq', taus=taus)    
        i = np.argwhere(taus_ < max(taus_) / 1)
        for tau, dev, err in zip(taus_[i], devs_[i], errs_[i]):
            err_l, err_h = adev_errs(tau, dev, data_length=len(signal.detrend(freqs['diffb'],type='constant') / 429e12), T_cyc=cycle_time) #compute error bars
            ax[1,1].plot(tau, dev, 'o' , color=colors['diffb'], label='zeeman B')
            ax[1,1].plot([tau, tau], [err_l, err_h], '-',color=colors['diffb'])          

        
    ax[1,1].set_yscale('log')
    ax[1,1].set_xscale('log')    
    #ax[1,1].legend(loc='best')
    ax[1,1].set_ylabel('ADev (ctrl + err)')
    #ax[1,1].set_xlabel('$\\tau$')
    ax[1,1].set_xlabel('Averaging Time (s)')
    
       
    """ subplot 0,2 errors"""
    for k, v in errs_raw.items():
        ax[0,2].plot(v, color='silver')
        if good_indicies:
            ax[0,2].plot(good_indicies, v[good_indicies], color=colors[k])
        ax[0,2].set_xlabel('Cycle Index')
        ax[0,2].set_ylabel('Error Signal ($\\delta P$)')
        ax[0,2].set_ylim([-1, 1])
        
    """ subplot 2,0 magnetic fields """
    ax[2,0].plot(freqs_raw['diffa'], color=colors['rawa'])
    if good_indicies:
        ax[2,0].plot(good_indicies,freqs['diffa'], color=colors['diffa'],linestyle='',marker='.')
    ax[2,0].plot(freqs_raw['diffb']+offset, color=colors['rawb'])
    if good_indicies:
        ax[2,0].plot(good_indicies,freqs['diffb']+offset, color=colors['diffb'],linestyle='',marker='.')
    ax[2,0].set_ylabel('Delta [Hz]')
    ax[2,0].set_xlabel('Cycle Index')


    """ subplt 1,2 """
    #BUG FIX: only plot binned data and report reduced chi-squared if we have sufficient data
    if len(shifts['density_shift']) > 2*binsize:
        ax[1,2].errorbar(shifts['bin_index'],shifts['density_bin_means'],shifts['density_bin_stds'],linestyle='',marker='o',color='k')
        ax[1,2].legend(['Chi-Squared = %.2f'%(shifts['density_chisquared'])])
    ax[1,2].plot(good_indicies,shifts['density_shift'],linestyle='',marker='.',color=colors['dens'])
    ax[1,2].set_ylabel('Density (N = %.0f)'%(runAtoms))
    ax[1,2].set_xlabel('Cycle Index')

    # Compute and plot the Allan Deviation of the error signal, stability, and density shift

    if taus and good_indicies:
        delta_errs = (errs_Hz['meana']-errs_Hz['meanb'])/np.sqrt(2)
        self_stability = (mean_no_drift_A + errs_Hz['meana'] - mean_no_drift_B - errs_Hz['meanb'])/np.sqrt(2)
        dens_shift = shifts['density_shift']
        #dens_shift = (mean_no_drift_A-mean_no_drift_B)/lever_arm
        (taus_err, devs_err, errs_err, n) = allantools.oadev(signal.detrend(delta_errs ,type='constant') / 429e12,
                                        rate=1. / (cycle_time), data_type='freq', taus=taus)
        err_err_l, err_err_h = adev_errs(taus_err, devs_err, data_length=len(delta_errs), T_cyc=cycle_time)
        
        (taus_stab, devs_stab, errs_stab, n) = allantools.oadev(signal.detrend(self_stability,type='constant' )/ 429e12,
                                        rate=1. / (cycle_time), data_type='freq', taus=taus)
        err_stab_l, err_stab_h = adev_errs(taus_stab, devs_stab, data_length=len(self_stability), T_cyc=cycle_time)
        
        (taus_dens, devs_dens, errs_dens, n) = allantools.oadev(signal.detrend(dens_shift,type='linear') ,
                                        rate=1. / (cycle_time), data_type='freq', taus=taus)
        err_dens_l, err_dens_h = adev_errs(taus_dens, devs_dens, data_length=len(dens_shift), T_cyc=cycle_time)
        
        i = np.argwhere(taus_err < max(taus_err) / 1)
        k = np.argwhere(taus_stab < max(taus_stab) / 1)
        j = np.argwhere(taus_dens < max(taus_dens) /1)

                
        fitend = np.round(len(taus_stab)/1)

        #Only fit stability if there are a few points to fit
        if fitend > (fitstart+2):
            fit_stab = fit_adev(taus_stab[fitstart:fitend],devs_stab[fitstart:fitend])
            ax[2,1].plot(taus_stab, fit_stab/np.sqrt(taus_stab),'--r')
            
        for m in j:
            ax[2,1].plot(taus_dens[m], devs_dens[m], 'o' ,color=colors['dens'], label='density = %.2E'%(density_shift))
            ax[2,1].plot([taus_dens[m],taus_dens[m]], [err_dens_l[m], err_dens_h[m]], color=colors['dens'])
        
        if fitend > (fitstart+2):
            ax[2,1].legend(['%1.2e /sqrt(tau)'%(fit_stab),'density = %.2E'%(density_shift)])
        for m in k:
            ax[2,1].plot(taus_stab[m], devs_stab[m], 'o' ,color=colors['stab'], label='stability')
            ax[2,1].plot([taus_stab[m],taus_stab[m]], [err_stab_l[m], err_stab_h[m]], color=colors['stab'])
        for m in i:
            ax[2,1].plot(taus_err[m], devs_err[m], 'o' ,color=colors['err'], label='error')
            ax[2,1].plot([taus_err[m],taus_err[m]], [err_err_l[m], err_err_h[m]], color=colors['err'])
            
        #mag_err, freq_err = psd(signal.detrend(delta_errs,type='constant')/429.0e12, NFFT = len(delta_errs),
        #            Fs= 1. / (cycle_time), window=plt.mlab.window_hanning)
        #ax[2,2].plot(freq_err, mag_err,color=colors['err'])

        #Add reference line for stability
        ax[2,1].plot(taus_stab, stability_1sec/np.sqrt(taus_stab),'--k')
        
        #Fit 1/rt(tau) slope to stability
        
    ax[2,1].set_yscale('log')
    ax[2,1].set_xscale('log')    
    ax[2,1].set_ylabel('Stability ADev (1/Hz)')
    ax[2,1].set_xlabel('Averaging Time (s)')

    if plot_diff == False:
        #Plot histogram of density shift data
        ax[2,2].hist(shifts['density_shift'].tolist(),bins=20)    
        ax[2,2].set_yscale('linear')
        ax[2,2].set_xscale('linear')    
        #ax[2,2].legend(loc='best')
        ax[2,2].set_ylabel('Counts')
        ax[2,2].set_xlabel('Density Shift (N = %.0f)'%(runAtoms))
    else:
        #Plot the timeseries of the difference between the two locks with and without cuts
        #Useful for deglitching data
        diff_freqs = freqs['meana'] - freqs['meanb']
        raw_diff_freqs = freqs_raw['meana']-freqs_raw['meanb']
        ax[2,2].plot(raw_diff_freqs, color=colors['rawa'])
        if good_indicies:  #only perform this step if there's uncut data
            ax[2,2].plot(good_indicies,diff_freqs, color=colors['stab'],linestyle='',marker='.')
        ax[2,2].set_ylabel('Conditional Shift (Hz)')
        ax[2,2].set_xlabel('Cycle Index')
    
    return fig, ax

    
def plot_density_shift(settings):
    import os
    import sys
    # Add J/data/date/notebooks/ to path    
    parent_dir = os.path.split(os.path.split(settings['plotter_path'])[0])[0]
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    # Import the desired data_tools modules from added path
    import data_tools.helpers
    reload(data_tools.helpers)
    from data_tools.helpers import *
        
    #Default file for BBR corrections.  Should be updated periodically
    #default_bbr = '/media/z/Sr1Software/ClockComparisonFall2017/TempControl/AllInOne/Data/TempLog_Keithley20_181024.txt'
    
    datapath = settings.get('data_path')
    #bbr_path = settings.get('bbr_path',default_bbr)
    f0 = settings.get('f0', 0)
    #adevcuts = settings.get('adevcuts', (0, None))  #No longer used
    cuts_A = settings.get('atomcuts_A', 200)
    cuts_B = settings.get('atomcuts_B', 200)
    atoms_normal = settings.get('runAtoms',1000.)
    data_cuts = settings.get('cuts', [(0, None)])
    stability = settings.get('stability',9.5e-17)
    binSize = settings.get('binsize',50)
    pmt_gain = settings.get('pmt_gain',10.0)
    cal_gain5 = settings.get('cal_gain5',0.111)
    bbr_cor = settings.get('bbr_corrections', False)
    zeeman2_cor = settings.get('z2_corrections', False)
    
    #Sometimes I manually override some values for convenience
    data_cuts = [(10,None)]
    cuts_A = 5.
    cuts_B = 5.
    pmt_gain = 1.
    atoms_normal = 100000.
    binSize = 20
    
    #Load data without applying any cuts
    data = load_data(datapath, ['conductor', 'blue_pmt'], cuts=[(5*4, None)])    
   
    #Apply cuts inside of process_clock_lock instead
    data = _process_density_shift(data,
                         cycle_time=None,
                         cutoff_A=cuts_A,
                         cutoff_B=cuts_B,
                         cuts=data_cuts,
                         #calGain5 = cal_gain5,
                         pmtGain=pmt_gain,
                         runAtoms=atoms_normal,
                         zeeman2_coeff = -0.2456e-6, #Hz/Hz^2, shouldn't change
                         binsize = binSize,
                         point_by_point = False, #Apply 2nd order zeeman corrections before computing density shift
                         use_bbr = False,) #Correct mean frequencies for shift, only necessary if data is being used to get Si frequency
                        
    
    fig,ax = _plot_density_shift(data, 
                                f0,
                                stability_1sec = stability, 
                                taus='octave',
                                point_by_point=False, #Plot the stabilities w point-by-point corrections
                                plot_diff = False,
                                fitstart=1)
    fig.tight_layout()
    
    return fig
