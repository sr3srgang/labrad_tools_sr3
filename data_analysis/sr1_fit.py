import numpy  as np
from scipy.optimize import curve_fit
from scipy.optimize import brentq

def fit(function, p_dict, x, y, y_err=None, p_fix=[]):
    """ make scipy.curve_fit easier to use 
    
    Args:
        function: function to be fit. 
            pass function parameters to first call. 
            pass variable to second call.
            e.g. 
            def linear(p):
                return lambda x: p['a'] * x + p['b']
        p_dict: dictionary mapping parameter names to values.
            e.g.
            p = {'a': 1e-2, 'b': 0}
        x: array of independent data
        y: array of dependent data
        y_err: array of errorbars for y
        p_fix: list of parameter names. 
            all other parameters will be optimized by curve_fit.
    Returns:
        solutions: dictionary mapping parameter names to optimized values.
        errors: dictionary mapping parameter names to std errors of fit.
    """
    p_dict = p_dict.copy()

    fit_these = [p for p in p_dict if p not in p_fix]
    def f(x, *pfit):
        p_all = p_dict.copy()
        p_all.update({p: v for p, v in zip(sorted(fit_these), pfit)})
        return function(p_all)(x)

    pfit = [v for (p, v) in sorted(p_dict.items()) if p in fit_these]
    if y_err is not None:
        popt, pcov = curve_fit(f, x, y, pfit, sigma=y_err, absolute_sigma=True)
    else:
        popt, pcov = curve_fit(f, x, y, pfit, sigma=y_err, absolute_sigma=False)
    perr = np.sqrt(np.diag(pcov))

    solutions = p_dict
    solutions.update({p: v for p, v in zip(sorted(fit_these), popt)})
    errors = {p: 0 for p in p_dict.keys()}
    errors.update({p: v for p, v in zip(sorted(fit_these), perr)})
    
    return solutions, errors




def fit_fig(fig, func, p_guess={}, p_fix=[], fit_range=[0, None], do_print=0, show_guess=0, fig_choice=0, color='r'):
    p_guessed = p_guess.copy()
    try:
        ax = fig.get_axes()[fig_choice]
        indi, indf = fit_range
        x, y = ax.get_lines()[-1].get_xydata()[indi:indf].T
        p_fit, p_err = fit(func, p_guess, x, y, p_fix=p_fix)
        x_fit = np.linspace(x.min(), x.max(), 1000)
        if show_guess:
            raise Exception
        ax.plot(x_fit, func(p_fit)(x_fit),color)
        
        # make fit values easier to read
        p_fit = {k: v
            for k, v in p_fit.items()}
        p_err = {k: v for k, v in p_err.items()}
        if do_print:
            print('-------- fit results --------')
            print('fit: ', p_fit)
            print('err: ', p_err)
        return p_fit, p_err
    except RuntimeError:
        print('bad fit')
        x_fit = np.linspace(x.min(), x.max(), 1000)
        ax.plot(x_fit, func(p_guessed)(x_fit), 'r--')
        return p_guessed, p_guessed
    except Exception as e:
        print(e)
        x_fit = np.linspace(x.min(), x.max(), 1000)
        ax.plot(x_fit, func(p_guessed)(x_fit), 'r--')
        return p_guessed, p_guessed

""" 
fit functions
"""
def exponential(p):
    return lambda x: p['b'] + p['a'] * np.exp(-x / p['tau'])

def lorentzian(p):
    return lambda f: p['a'] / (1.0 + (2.0 * (f - p['x0']) / p['Gamma'])**2) + p['b']

def gaussian(p):
    return lambda f: p['a'] * np.exp((-1./ 2.) * ((f - p['x0'])/ p['sigma'])**2.) + p['b']

def linear(p):
    return lambda x: p['a'] * x + p['b']

def sine(p):
    a = p.get('a', 1)
    b = p.get('b', 0)
    f = p.get('f', 1)
    phi = p.get('phi', 0)
    return lambda t: a * np.sin(2 * np.pi * f * t + phi) + b

def sine_exp(p):
    a = p.get('a', 1)
    b = p.get('b', 0)
    f = p.get('f', 1)
    phi = p.get('phi', 0)
    tau = p.get('tau', np.inf)
    return lambda t: a * np.exp(-t / tau) * np.sin(2 * np.pi * f * t + phi) + b

def sin2(p):
    return lambda y: p['a'] * np.sin(np.pi * y / p['c'] + p['phi']) + p['b']
    
def rabi(p):
    O0 = p.get('Omega', 1)
    T = p.get('T', 1)
    a = p.get('a', 1)
    b = p.get('b', 0)
    x0 = p.get('x0', 0)
    
    def r(x):
        O = np.sqrt(O0**2 + (2 * np.pi * (x - x0))**2)
        return a * O0**2 * np.sin(O * T / 2.)**2 / O**2 + b
    return r
    
def radial(p):
    O0 = p.get('Omega', 1)
    T = p.get('T', 1)
    a = p.get('a', 1)
    b = p.get('b', 0)
    x0 = p.get('x0', 0)

    amp = p.get('amp', 1)
    f_rad = p.get('f_rad', 100)
    sigma = p.get('sigma', 10)
    
    def rabi(x):
        O = np.sqrt(O0**2 + (2 * np.pi * (x - x0))**2)
        return a * O0**2 * np.sin(O * T / 2.)**2 / O**2 + b
    def gaussians(x):
        return (amp * np.exp((-1./ 2.) * ((x - (p['x0'] + f_rad))/ p['sigma'])**2.) 
                    + amp * np.exp((-1./ 2.) * ((x - (p['x0'] - f_rad))/ p['sigma'])**2.))
    def f(x):
        return rabi(x) + gaussians(x)

    return f


def rabi10x(p):
    O0 = p.get('Omega', 1)
    T = p.get('T', 1)
    a = p.get('a', 1)
    p1 = p.get('p1', 1)
    p2 = p.get('p2', 1)
    p3 = p.get('p3', 1)
    p4 = p.get('p4', 1)
    p5 = p.get('p5', 1)
    p6 = p.get('p6', 1)
    p7 = p.get('p7', 1)
    p8 = p.get('p8', 1)
    p9 = p.get('p9', 1)
    p10 = p.get('p10', 1)
    b = p.get('b', 0)
    x0 = p.get('x0', 0)
    B0 = p.get('B0', 0)
    
    def r(x, cg):
        O = np.sqrt(cg*O0**2 + (2 * np.pi * (x - x0))**2)
        return a * cg * O0**2 * np.sin(O * T / 2.)**2 / O**2
        
    def r10(x):
        return np.abs(p1)*r(x + B0, 0.82) + np.abs(p2)*r(x + (7./9.)*B0, 0.49) + np.abs(p3)*r(x + (5./9.)*B0, 0.25) + np.abs(p4)*r(x + (3./9.)*B0, 0.09) + np.abs(p5)*r(x + (1./9.)*B0, 0.01) + np.abs(p6)*r(x - (1./9.)*B0, 0.01) + np.abs(p7)*r(x - (3./9.)*B0, 0.09) + np.abs(p8)*r(x - (5./9.)*B0, 0.25) + np.abs(p9)*r(x - (7./9.)*B0, 0.49) + np.abs(p10)*r(x - B0, 0.82) + b
    return r10
    
def rabi8x(p):
    O0 = p.get('Omega', 1)
    T = p.get('T', 1)
    a = p.get('a', 1)
    p1 = p.get('p1', 1)
    p2 = p.get('p2', 1)
    p3 = p.get('p3', 1)
    p4 = p.get('p4', 1)
    p7 = p.get('p7', 1)
    p8 = p.get('p8', 1)
    p9 = p.get('p9', 1)
    p10 = p.get('p10', 1)
    b = p.get('b', 0)
    x0 = p.get('x0', 0)
    B0 = p.get('B0', 0)
    
    def r(x, cg):
        O = np.sqrt(cg*O0**2 + (2 * np.pi * (x - x0))**2)
        return a * cg * O0**2 * np.sin(O * T / 2.)**2 / O**2
        
    def r8(x):
        return np.abs(p1)*r(x + B0, 0.82) + np.abs(p2)*r(x + (7./9.)*B0, 0.49) + np.abs(p3)*r(x + (5./9.)*B0, 0.25) + np.abs(p4)*r(x + (3./9.)*B0, 0.09) + np.abs(p7)*r(x - (3./9.)*B0, 0.09) + np.abs(p8)*r(x - (5./9.)*B0, 0.25) + np.abs(p9)*r(x - (7./9.)*B0, 0.49) + np.abs(p10)*r(x - B0, 0.82) + b
    return r8
    
def rabi6x(p):
    O0 = p.get('Omega', 1)
    T = p.get('T', 1)
    a = p.get('a', 1)
    p1 = p.get('p1', 1)
    p2 = p.get('p2', 1)
    p3 = p.get('p3', 1)
    p8 = p.get('p8', 1)
    p9 = p.get('p9', 1)
    p10 = p.get('p10', 1)
    b = p.get('b', 0)
    x0 = p.get('x0', 0)
    B0 = p.get('B0', 0)
    
    def r(x, cg):
        O = np.sqrt(cg*O0**2 + (2 * np.pi * (x - x0))**2)
        return a * cg * O0**2 * np.sin(O * T / 2.)**2 / O**2
        
    def r6(x):
        return np.abs(p1)*r(x + B0, 0.82) + np.abs(p2)*r(x + (7./9.)*B0, 0.49) + np.abs(p3)*r(x + (5./9.)*B0, 0.25) + np.abs(p8)*r(x - (5./9.)*B0, 0.25) + np.abs(p9)*r(x - (7./9.)*B0, 0.49) + np.abs(p10)*r(x - B0, 0.82) + b       
    return r6
    
def axialTemp(p):
	b = p.get('b', 0)
	ampRed = p.get('ampRed', 0.1)
	ampCarrier = p.get('ampCarrier', 0.5)
	ampBlue = p.get('ampBlue', 0.1)
	x0 = p.get('x0', 0)
	vz = p.get('vz', 80)
	alpha = p.get('alpha', 1)
	sigma = p.get('sigma', 1)
	
	def red(x):
		return ampRed*(1+(x-x0)/vz)*np.heaviside((x-x0) + vz,1)*np.heaviside((x0-x),1)*np.exp(-alpha*(1+(x-x0)/vz))
	
	def blue(x):
		return ampBlue*(1-(x-x0)/vz)*np.heaviside(vz - (x-x0),1)*np.heaviside((x-x0),1)*np.exp(-alpha*(1-(x-x0)/vz))
	
	def carrier(x):
		return ampCarrier*np.exp((-1/2)*((x-x0)/sigma)**2)
	
	def summedPeaks(x):
		return red(x) + blue(x) + b + carrier(x)
		
	return summedPeaks

def processAxialTemp(f, soln): #this data processing function takes the solution of the axialTemp fitter above as the input argument
	def red(x):
		return soln["ampRed"]*(1+(x-soln["x0"])/soln["vz"])*np.heaviside((x-soln["x0"]) + soln["vz"],1)*np.heaviside((soln["x0"]-x),1)*np.exp(-soln["alpha"]*(1+(x-soln["x0"])/soln["vz"]))
	
	def blue(x):
		return soln["ampBlue"]*(1-(x-soln["x0"])/soln["vz"])*np.heaviside(soln["vz"] - (x-soln["x0"]),1)*np.heaviside((x-soln["x0"]),1)*np.exp(-soln["alpha"]*(1-(x-soln["x0"])/soln["vz"]))
	
	# Because the background integrated over the whole spectrum can be comparable to the area under the red sideband, we limit the frequencies we integrate over to limit the effect of small fluctuations in the background value
#	redFreqs = freqs[np.nonzero(freqs*np.heaviside((freqs-soln["x0"]) + np.abs(soln["vz"]),1)*np.heaviside((soln["x0"]-freqs),1))]
#	blueFreqs = freqs[np.nonzero(freqs*np.heaviside(np.abs(soln["vz"]) + (freqs-soln["x0"]),1)*np.heaviside((freqs-soln["x0"]),1))]
#	areaRed = np.trapz(red(redFreqs) - soln["b"], redFreqs, np.abs(freqs[0]-freqs[1]))
#	areaBlue = np.trapz(blue(blueFreqs) - soln["b"], blueFreqs, np.abs(freqs[0]-freqs[1]))
	areaRed = np.trapz(red(f), f, np.abs(f[0]-f[1]))
	areaBlue = np.trapz(blue(f), f, np.abs(f[0]-f[1]))
	ratioRB = np.abs(areaRed/areaBlue)

	print('Red/Blue sideband area: ' + str(np.round(ratioRB,3)))
	print('')

	kHz2uK = 0.047992
	f_rec = 3.46581 # in units of kHz
	f_tot = soln["vz"] + f_rec # also in units of kHz
	
	def HO_Energy(n):
		energy = f_tot*(n + 0.5) - f_rec*0.5*(n**2 + n + 1)
		return energy
	
	def partitionFunction(x):
		return (np.exp(-HO_Energy(0)*kHz2uK/x) + np.exp(-HO_Energy(1)*kHz2uK/x) + np.exp(-HO_Energy(2)*kHz2uK/x) + np.exp(-HO_Energy(3)*kHz2uK/x) + np.exp(-HO_Energy(4)*kHz2uK/x) + np.exp(-HO_Energy(5)*kHz2uK/x) + np.exp(-HO_Energy(6)*kHz2uK/x))
	
	# Now finding the temperature from the zeros of this function	
	def rootEqn(x):
		return 1 - ratioRB - (np.exp(-HO_Energy(0)*kHz2uK/x))/partitionFunction(x)
		
	guess = [0.1, 100.0]
	guess0 = rootEqn(guess[0])
	guess1 = rootEqn(guess[1])
	if np.sign(guess0)==np.sign(guess1):
		tempZ = 0.1
	elif np.sign(guess0)!=np.sign(guess1):
		tempZ = brentq(rootEqn, guess[0], guess[1])
	
	# Level occupation probabilities
	def occupationNumbers(n):
		return np.exp(-HO_Energy(n)*kHz2uK/tempZ)/partitionFunction(tempZ)
	
	p0 = occupationNumbers(0)
	p1 = occupationNumbers(1)
	p2 = occupationNumbers(2)
	p3 = occupationNumbers(3)
	p4 = occupationNumbers(4)

    
	nzBar = np.sum([n*occupationNumbers(n) for n in range(10)])
	
	return tempZ, p0, p1, p2, p3, p4, nzBar

def ramsey(p):
    tPi2 = p.get('tPi2', 1)
    tDark = p.get('tDark', 1)
    a = p.get('a', 1)
    x0 = p.get('x0', 0)
    b = p.get('b', 0.01)
    amp = p.get('amp', 1)
    f_rad = p.get('f_rad', 100)
    sigma = p.get('sigma', 10)
    
    def fringes(x):
        omega0 = np.pi/(2*tPi2)
        omega = np.sqrt(omega0**2 + (2 * np.pi * (x - x0))**2)
        return a * (omega0**2/omega**4)*(omega*np.cos(np.pi*(x-x0)*tDark)*(np.sin(np.pi*omega/(2.*omega0))) - 4*np.pi*(x-x0)*np.sin(np.pi*(x-x0)*tDark)*(np.sin(np.pi*omega/(4*omega0)))**2)**2 + b
        
    def gaussians(x):
        return (amp * np.exp((-1./ 2.) * ((x - (p['x0'] + f_rad))/ p['sigma'])**2.) 
                    + amp * np.exp((-1./ 2.) * ((x - (p['x0'] - f_rad))/ p['sigma'])**2.))
    def f(x):
        return fringes(x) + gaussians(x)

    return f


















