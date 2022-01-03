import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import pylab
from matplotlib.ticker import NullFormatter
import matplotlib.patches as patches
#import data_analysis.live_plotter as lp


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
    #astropy
    exp_val = ((sigma_y*(x - x0))**2 - 2*p*sigma_x*sigma_y*(x - x0)*(y - y0) + (sigma_x*(y - y0))**2)/((1 - p**2)*(sigma_x*sigma_y)**2)
    return A * np.exp(-exp_val/2) + offset
    
def fit_gaussian_form(X, A, x0, y0, sigma_x, sigma_y, p, offset):
    x, y = X
    return gaussian_2D(x, y, A, x0, y0, sigma_x, sigma_y, p, offset).flatten() 
    

def visualize_mot_image(mot_array, show_plot = True, c_max = 200, show_title = False, title = None):
    #From example here: https://matplotlib.org/examples/pylab_examples/scatter_hist.html
    nullfmt = NullFormatter()
    
    y_len, x_len = mot_array.shape
    
    left, width = .1, .75
    bottom, height = .1, .75
    left_h = left + width + .02
    bottom_h = left + height + .02
    
    rect_imshow = [left, bottom, width, height]
    rect_histx = [left + .03, bottom_h, width - .06, .1*x_len/y_len]
    rect_histy = [left_h, bottom, .1, height]

    emp_width = 6.5
    spacer= .5
    emp_height = (emp_width - spacer)*y_len/x_len - spacer
    fig = plt.figure(1, figsize=(emp_width, emp_height))
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
    axImshow.tick_params(color='white', labelcolor='white', labelsize=12)
    im.set_clim(0, c_max)
    if show_title:
        axImshow.set_title("{:.3e}".format(title), color = 'w', y = .85, size = 48)
        
    #side histograms:
    xs = np.sum(mot_array, axis = 0)
    ys = np.sum(mot_array, axis = 1)
    axHistx.plot(xs, 'white')
    axHistx.set_xlim(axImshow.get_xlim())
    #axHistx.set_ylim(0, ylim)
    axHisty.plot(ys, np.arange(len(ys)), 'white')
    axHisty.set_ylim(axImshow.get_ylim())
    #axHisty.set_xlim(0, xlim)
    
    if show_plot:
    	plt.show()
    	
    return fig, axImshow, [x_len, y_len, emp_width*100, emp_height*100]
    
def return_cuts(mot_array, show_plot = True, c_max = 200, show_title = False, title = None):
    #From example here: https://matplotlib.org/examples/pylab_examples/scatter_hist.html
    nullfmt = NullFormatter()
    
    y_len, x_len = mot_array.shape
    
    left, width = .1, .75
    bottom, height = .1, .75
    left_h = left + width + .02
    bottom_h = left + height + .02
    
    rect_imshow = [left, bottom, width, height]
    rect_histx = [left + .03, bottom_h, width - .06, .1*x_len/y_len]
    rect_histy = [left_h, bottom, .1, height]

    emp_width = 6.5
    spacer= .5
    emp_height = (emp_width - spacer)*y_len/x_len - spacer
    fig = plt.figure(1, figsize=(emp_width, emp_height))
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
    axImshow.tick_params(color='white', labelcolor='white', labelsize=12)
    im.set_clim(0, c_max)
    if show_title:
        axImshow.set_title("{:.3e}".format(title), color = 'w', y = .85, size = 48)
        
    #side histograms:
    xs = np.sum(mot_array, axis = 0)
    ys = np.sum(mot_array, axis = 1)
    axHistx.plot(xs, 'white')
    axHistx.set_xlim(axImshow.get_xlim())
    #axHistx.set_ylim(0, ylim)
    axHisty.plot(ys, np.arange(len(ys)), 'white')
    axHisty.set_ylim(axImshow.get_ylim())
    #axHisty.set_xlim(0, xlim)
    
    if show_plot:
    	plt.show()
    	
    return xs, ys

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
        _, axImshow = visualize_mot_image(mot_image, show_plot = False)
        A, x0, y0, sigma_x, sigma_y, p, offset = vals
        #NOTE: plotted sigma curves don't take into account covariance!! These are a diagnostic tool ONLY
        sig1 = gaussian_2D(x0, y0 + sigma_y, A, x0, y0, sigma_x, sigma_y, p, offset)
        sig2 = gaussian_2D(x0, y0 + 2*sigma_y, A, x0, y0, sigma_x, sigma_y, p, offset)
        print(sig1, sig2)
        axImshow.contour(gaussian_2D(x, y, *vals), colors = 'gray', levels = (sig2, sig1))
        plt.show()
        #plt.title('A = {:.4f} +/- {:.4f}'.format(vals[0], np.sqrt(pcov[0, 0])), fontsize = 20)
    return vals, np.sqrt(np.diag(pcov))
    
def process_file(mot_img, zoom = False, ROI = None, background = None):
    mot_image = cv2.imread(mot_img, 0).T.astype(np.int16)
    if background is not None:
        background = cv2.imread(background, 0).T.astype(np.int16)
        mot_image = mot_image - background
    if zoom:
        mot_image = mot_image[ROI[1]:ROI[1]+ROI[3], ROI[0]:ROI[0]+ROI[2]]
    return mot_image
    
def process_file_return_background(mot_img, zoom = False, ROI = None, background = None):
    mot_image = cv2.imread(mot_img, 0).T.astype(np.int16)
    
    if background is not None:
        background = cv2.imread(background, 0).T.astype(np.int16)
        mot_image = mot_image - background
    if zoom:
        mot_image = background[ROI[1]:ROI[1]+ROI[3], ROI[0]:ROI[0]+ROI[2]]
    return mot_image

def default_window(mot_img, rot = 0, show_title = False, title = None, zoom = False, ROI = None, background = None):
    mot_image = process_file(mot_img, zoom, ROI, background)
    mot_image = np.rot90(mot_image, rot)
    fig, axImshow, dims = visualize_mot_image(mot_image, show_plot = False, show_title = show_title, title = title)
    return fig, axImshow, dims
    
def save_gui_window(mot_img, save_loc, ROI, rot = 0, show_title = False, title = None, zoom = False, background = None):
    fig, _ , dims= default_window(mot_img, rot = rot, show_title = show_title, title = title, zoom = zoom, ROI = ROI, background = background)
    fig.savefig(save_loc)
    plt.close()
    return dims

def save_gui_window_ROI(mot_img, save_loc, ROI, rot = 0, show_title = False, title = None,zoom = False, background = None):
    print(mot_img)
    fig, axImshow, dims = default_window(mot_img, rot = rot, show_title = show_title, title = title, zoom = zoom, ROI = ROI, background = background)
    if not zoom:
        rect = patches.Rectangle((ROI[0], ROI[1]),ROI[2],ROI[3],linewidth=1,edgecolor='pink',facecolor='none')
        axImshow.add_patch(rect)
    fig.savefig(save_loc)
    plt.close()
    return dims

'''
MM Modified 070221 for new camera gui from here on:
'''
   
def fig_gui_window_ROI(mot_img, ax, ROI, rot = 0, show_title = False, title = None, zoom = False, background = None):
    print(mot_img)
    mot_image = process_file(mot_img, zoom, ROI, background)
    mot_image = np.rot90(mot_image, rot)
    fig_visualize_mot_image(mot_image, ax, show_title = show_title, title = 'testing')
    '''
    fig, axImshow, dims = default_window(mot_img, rot = rot, show_title = show_title, title = title, zoom = zoom, ROI = ROI, background = background)
    if not zoom:
        rect = patches.Rectangle((ROI[0], ROI[1]),ROI[2],ROI[3],linewidth=1,edgecolor='pink',facecolor='none')
        axImshow.add_patch(rect)
    fig.savefig(save_loc)
    plt.close()
    return dims    
    '''
    
def fig_visualize_mot_image(mot_array, axImshow, c_max = 100, show_title = False, title = None):
    axImshow.clear()
    #center imshow:
    im = axImshow.imshow(mot_array, cmap = 'magma', origin = 'lower', aspect = 'equal')
    axImshow.tick_params(color='white', labelcolor='white', labelsize=12)
    im.set_clim(0, c_max)
    if show_title:
        axImshow.set_title("{:.3e}".format(title), color = 'w', y = .85, size = 48)

       
def fig_plotter(mot_img, ROI):
    mot_image = process_file(mot_img, ROI = ROI, zoom = True)
    return np.sum(mot_image)

def fig_exc(gnd_path, ROI):
    #It gets sent the gnd image; also find and read in exc and background
    exc_path = gnd_path.replace('gnd', 'exc')
    background_path = gnd_path.replace('gnd', 'background')

    gnd_sub = process_file(gnd_path, ROI = ROI, zoom = True, background = background_path)
    exc_sub = process_file(gnd_path, ROI = ROI, zoom = True, background = background_path)

    #Get conductor file
    str_end = '_fluorescence.png'
    keyword = 'fluor_'
    split_str = gnd_path.partition(str_end)
    parse_name = split_str[0].partition(keyword)
    beginning = parse_name[0]
    shot_num = int(parse_name[-1])
    f_name = "{}.conductor.json".format(shot_num)
    #path = os.path.join(settings['data_path'], settings['exp_name'], f_name)
    #f = open(path)
    #c_json = json.load(f)
    #freq = c_json['clock_sg380']
    
    return lp.calc_excitation(np.sum(gnd_sub), np.sum(exc_sub))
    
    
