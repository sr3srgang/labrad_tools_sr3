def gaussian(x, mu, sig,a, b):
    return a*np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.))) + b

def process_rabi_data(excs, freqs, p0, show_p0 = False):
    cen_freqs = freqs - np.mean(freqs)
    
    popt, pcov = curve_fit(gaussian, cen_freqs, excs, p0 = p0)

