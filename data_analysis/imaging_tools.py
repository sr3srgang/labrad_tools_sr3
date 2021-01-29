import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

path_to_data = 'home/srgang/K/data/data'

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

def fit_gaussian_2D_real(mot_img, background_file = None, p0 = [.53, 0, .4, .5, .7, .005, 0], show_plot = False, show_guess = False):
    mot_image = imread(mot_img)
    
    if background_file is not None:
        background = imread(background_file)
        mot_image -= background
    #mot_image = mot_image[:, :, 2] #extracting "blue" channel of png (though I think RGB all identical for this camera)

    y_pix, x_pix = mot_image.shape
    print(y_pix)
    y_grid = np.linspace(0, y_pix, y_pix)
    x_grid = np.linspace(0, x_pix, x_pix)
    x, y = np.meshgrid(x_grid, y_grid)
    
    if show_guess:
        plt.figure()
        plt.imshow(mot_image, cmap = 'magma')
        plt.contour(gaussian_2D(x, y, *p0), cmap = 'gray')
    vals, pcov = curve_fit(fit_gaussian_form, (x, y), mot_image.flatten(), p0)

    #clear_output(wait=True)
    if show_plot:
        plt.figure()
        plt.imshow(mot_image, cmap = 'magma')
        if c_max is not None:
            plt.clim(0, c_max)
        plt.colorbar()
        plt.contour(gaussian_2D(x, y, *vals), cmap = 'gray', levels = 1)
        plt.title('A = {:.4f} +/- {:.4f}'.format(vals[0], np.sqrt(pcov[0, 0])), fontsize = 20)
    
    if contour_figure_ix is not None:
        plt.figure(contour_figure_ix)
        plt.contour(gaussian_2D(x, y, *vals), cmap = 'gray', levels = 1)
    
    return vals, np.sqrt(np.diag(pcov))
