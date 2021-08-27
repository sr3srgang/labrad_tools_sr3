import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from data_analysis.MM_analysis import pico_expt as pe

def fringe(f, A, w, phi, B):
    return A*np.sin(np.array(f)*w - phi)**2 + B

def process_ramsey_data(excs, freqs, p0, ax = None, show_p0 = False):
    cen_freqs = freqs #- np.mean(freqs)
    
    popt, pcov = curve_fit(fringe, cen_freqs, excs, p0 = p0)
    fringe_freq = popt[1]/(np.pi * 2)
    print("Extracted fringe freq from fit: {}".format(fringe_freq))
    print(popt)
    unc = np.sqrt(np.diag(pcov))
    #plt.figure()
    if ax is not None:
        #ax.plot(cen_freqs, excs, '.', color='k')
        ax.plot(cen_freqs, fringe(cen_freqs, *popt), '--', color = 'xkcd:dull pink')
        ax.set_title('Contrast: {:.1f} +/- {:.1f} %'.format(popt[0]*100, unc[0]*100), color = 'white')
        if show_p0:
            ax.plot(cen_freqs, fringe(cen_freqs, *p0))
    #plt.ylim((0, 1)).
    #plt.xlabel('Clock detuning (Hz)')
    #plt.ylabel('Excitation fraction')
    #plt.show()
    return popt, unc

def ramsey_fft(excs, freqs, popt, fringe_freq):
    plt.figure()
    plt.axvline(x= fringe_freq, color ='gray')
    Pxx, f = mlab.psd(excs - np.mean(excs), NFFT = len(excs), Fs = 1/np.mean(np.diff(freqs)), pad_to = 2**12)
    plt.plot(f, Pxx, 'k')
    plt.xlim((0, 1))
    plt.xlabel('Fringe frequency')
    plt.ylabel('Power (AU)')
    plt.show()
    
    plt.figure()
    acf = sm.tsa.acf(excs, nlags = len(excs), adjusted = True, fft=False)
    plt.plot(freqs[1:] - freqs[1], acf[1:], 'o', color = 'k')
    plt.xlabel('Frequency separation (Hz)')
    plt.ylabel('Autocorrelation')
    plt.axvline(x = 1/fringe_freq, color = 'gray')

def fit_phase_expt(data_path, exp_name, shots, ixs):
    _, excs, keys = pe.pico_expt(data_path, exp_name, shots, ixs, ['sequencer.clock_phase'])
    fig, ax = plt.subplots()
    phases = keys[:, 0]
    plt.plot(phases, excs, 'ok')
    return process_ramsey_data(excs, phases, p0 = [1, 2*np.pi/2, 0, 0], ax = ax)
    

def fit_ramsey(data_path, exp_name, shots, ixs, p0, show_p0 = False):
    excs, freqs, keys = pico_expt_exc(data_path, exp_name, shots, ixs)
    return process_ramsey_data(excs, freqs, p0, show_p0 = show_p0)
    
def fit_ramsey_fft(data_path, exp_name, shots, ixs, p0, show_p0 = False):
    excs, freqs = pico_expt_exc(data_path, exp_name, shots, ixs)
    popt, fringe_freq = process_ramsey_data(excs, freqs, p0, show_p0 = show_p0)
    ramsey_fft(excs, freqs, popt, fringe_freq)
    
