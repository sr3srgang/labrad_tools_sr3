import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import pylab
from matplotlib.ticker import NullFormatter

path_to_data = '/home/srgang/K/data/data'

def bin_reps(data_folder, first_file, n_reps, per_rep, global_path = False):
    '''
    bins files by ctime, given starting file, number of repititions, and number of files per repitition.
    assumes data_folder is given as YYYYMMDD/experiment unless global_path = True
    '''
    if not global_path:
        data_path = os.path.join(path_to_data, data_folder)
    else:
        data_path = data_folder

    files = glob.glob(os.path.join(data_folder, '*.png'))
    ix = argsort(f_times)
    files_sorted = files[ix][first_file::first_file + n_reps*per_rep]
    return np.reshape(files_sorted, (n_reps, per_rep))

def gaussian_2D(x, y, A, x0, y0, sigma_x, sigma_y, p, offset):
    exp_val = ((sigma_y*(x - x0))**2 - 2*p*sigma_x*sigma_y*(x - x0)*(y - y0) + (sigma_x*(y - y0))**2)/((1 - p**2)*(sigma_x*sigma_y)**2)
    return A * np.exp(-exp_val/2) + offset
    
def fit_gaussian_form(X, A, x0, y0, sigma_x, sigma_y, p, offset):
    x, y = X
    return gaussian_2D(x, y, A, x0, y0, sigma_x, sigma_y, p, offset).flatten() 
    

def visualize_mot_image(mot_array, show_plot = True, c_max = 200, ylim = 20e+3, xlim = 30e+3):
    #From example here: https://matplotlib.org/examples/pylab_examples/scatter_hist.html
    nullfmt = NullFormatter()
    
    y_len, x_len = mot_array.shape
    
    left, width = .1, .65
    bottom, height = .1, .65
    left_h = left + width + .02
    bottom_h = left + height + .02
    
    rect_imshow = [left, bottom, width, height]
    rect_histx = [left, bottom_h, width, .1]
    rect_histy = [left_h, bottom, .15, height]
    
    fig = plt.figure(1, figsize=(8, 8*y_len/x_len))
    fig.patch.set_facecolor('k')
    
    axImshow = plt.axes(rect_imshow)
    axHistx = plt.axes(rect_histx)
    axHisty = plt.axes(rect_histy)
    
    #turn off labels
    axHistx.xaxis.set_major_formatter(nullfmt)
    axHisty.yaxis.set_major_formatter(nullfmt)
    axHistx.set_facecolor('k')
    axHisty.set_facecolor('k')
    
    #center imshow:
    im = axImshow.imshow(mot_array, cmap = 'magma', origin = 'lower', aspect = 'equal')
    axImshow.tick_params(color='white', labelcolor='white', labelsize=20)
    im.set_clim(0, c_max)
    #side histograms:
    xs = np.sum(mot_array, axis = 0)
    ys = np.sum(mot_array, axis = 1)
    axHistx.plot(xs, 'white')
    axHistx.set_xlim(axImshow.get_xlim())
    axHistx.set_ylim(0, ylim)
    axHisty.plot(ys, np.arange(len(ys)), 'white')
    axHisty.set_ylim(axImshow.get_ylim())
    axHisty.set_xlim(0, xlim)
    
    if show_plot:
    	plt.show()
    	
    return fig, axImshow
    
    
    

def fit_gaussian_2D_real(mot_img, background_file = None, show_plot = False):
    mot_image = cv2.imread(mot_img, 0).T.astype(np.int16)
    
    if background_file is not None:
        background = cv2.imread(background_file, 0).T.astype(np.int16)
        mot_image -= background
	
    y_pix, x_pix = mot_image.shape
    y_grid = np.linspace(0, y_pix, y_pix)
    x_grid = np.linspace(0, x_pix, x_pix)
    x, y = np.meshgrid(x_grid, y_grid)
    
    x0_guess = np.argmax(np.sum(mot_image, axis = 0))
    y0_guess = np.argmax(np.sum(mot_image, axis = 1))
    A_guess = mot_image[y0_guess, x0_guess]
    p0 = [A_guess, x0_guess, y0_guess, 100, 100, -.2, 0]
    if show_plot:
        axImshow = visualize_mot_image(mot_image, show_plot = False)
        A, x0, y0, sigma_x, sigma_y, p, offset = vals
        #NOTE: plotted sigma curves don't take into account covariance!! These are a diagnostic tool ONLY
        sig1 = gaussian_2D(x0, y0 + sigma_y, A, x0, y0, sigma_x, sigma_y, p, offset)
        sig2 = gaussian_2D(x0, y0 + 2*sigma_y, A, x0, y0, sigma_x, sigma_y, p, offset)
        print(sig1, sig2)
        axImshow.contour(gaussian_2D(x, y, *vals), colors = 'gray', levels = (sig2, sig1))
        plt.show()
        #plt.title('A = {:.4f} +/- {:.4f}'.format(vals[0], np.sqrt(pcov[0, 0])), fontsize = 20)
    return vals, np.sqrt(np.diag(pcov))
    
    
    
def show_MOT_image(mot_img):
    mot_image = cv2.imread(mot_img, 0).T.astype(np.int16)
    fig, _ = visualize_mot_image(mot_img)
    return fig
    
    
    
    
    
    
    
    
