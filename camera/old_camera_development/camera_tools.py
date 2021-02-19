import os, glob, time, matplotlib, cv2, cmapy
import numpy as np
import matplotlib.pyplot as plt
from pylab import imread
from scipy.optimize import curve_fit

most_recent_file_time = 'start'

def get_today_path():
    time_string = time.strftime('%Y%m%d')
    return 'K:data/data/' + time_string + '/**'


def get_most_recent_file(directory, ext = '.png'):
    files = glob.glob(directory + "/*" + ext, recursive = True)
    try:
        return max(files, key = os.path.getmtime)
    except:
        pass

def auto_refresh_dir(script, ext = ['.png']):
    while True:
        try:
            this_dir = get_today_path()
            files = []
            for ending in ext:
                files.append(get_most_recent_file(this_dir, ending))
            script(files)
            cv2.waitKey(1)
        except (TypeError, SyntaxError, ValueError, IndexError) as e:
            pass
        except KeyboardInterrupt:
            break


def align_mot(img, background_file = None):
    mot_image = cv2.imread(img[0], 0)
    if background_file is not None:
        background = imread(background_file)
        mot_image -= background
    show_text = "{:.2f}*1e+7".format(np.sum(mot_image*1e-7))
    cv2.putText(mot_image, show_text, (200, 150), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 255, 255), 3) 
    cv2.imshow('align', mot_image)

def extract_ROI(img, background_file = None):
    mot_image = cv2.imread(img, 0)
    if background_file is not None:
        background = cv2.imread(background_file)
        mot_image -= background
    x0, y0 = ROI_start
    xf, yf = ROI_end
    return mot_image, mot_image[x0:xf, y0:yf]

def align_mot_ROI(mot_img, background_file = None):
    mot_image, ROI = extract_ROI(mot_img[0], background_file)
    show_text = "{:.2f}*1e+5".format(np.sum(ROI)*1e-5)
    cv2.rectangle(mot_image, ROI_start, ROI_end, (255, 105, 180), 5)
    cv2.putText(mot_image, show_text, (200, 150), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 255, 255), 3)
    cv2.imshow('align', mot_image)

def live_plot_ROI(mot_img, background_file = None):
    mot_image, ROI = extract_ROI(mot_img[0], background_file)
    empty_data = np.where(live_data == None)
    this_shot = np.sum(ROI)*1e-3
    if len(empty_data[0]) == 0:
        #shift plot back by one
        live_data[0:n_show - 1] = live_data[1:n_show]
        live_data[-1] = this_shot
    else:
        #while initially populating data array
        live_data[empty_data[0][0]] = this_shot
    plt.figure()
    plt.plot(live_data, 'o-k')
    plt.xlim((-1, n_show))
    plt.gcf().canvas.draw()
    img = np.frombuffer(plt.gcf().canvas.tostring_rgb(), dtype =np.uint8)
    img = img.reshape(plt.gcf().canvas.get_width_height()[::-1] + (3, ))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imshow('align_plot', img)
    plt.close()

def live_plot_ROI_shot(mot_img, background_file = None):
    global most_recent_file_time
    this_time = os.path.getmtime(mot_img[0])
    if not(this_time == most_recent_file_time):
        live_plot_ROI(mot_img, background_file = None)
        most_recent_file_time = this_time
    
def gaussian_2D(x, y, A, x0, y0, sigma_x, sigma_y, p, offset):
    exp_val = ((sigma_y*(x - x0))**2 - 2*p*sigma_x*sigma_y*(x - x0)*(y - y0) + (sigma_x*(y - y0))**2)/((1 - p**2)*(sigma_x*sigma_y)**2)
    N = 2*np.pi*np.sqrt(1 - p**2)*sigma_x*sigma_y
    return A * np.exp(-exp_val/2)/N + offset

def test_gaussian_2D(x, y, A, x0, y0, sigma_x, sigma_y, p, offset):
    '''
Equivalent to gaussian_2D, except with numerical diagonalization instead of analytical expression above.
From: https://stackoverflow.com/questions/28342968/how-to-plot-a-2d-gaussian-with-different-sigma
'''
    cov_mat = np.array([[sigma_x**2, p*sigma_x*sigma_y], [p*sigma_x*sigma_y, sigma_y**2]])
    det_cov = np.linalg.det(cov_mat)
    N = np.sqrt((2*np.pi)**2*det_cov)
    inv_cov = np.linalg.inv(cov_mat)

    mu = np.array([x0, y0])

    (ax1, ax2) = x.shape
    pos = np.zeros((ax1, ax2, 2))
    pos[:, :, 0] = x
    pos[:, :, 1] = y

    fac = np.einsum('...k,kl,...l->...', pos - mu, inv_cov, pos - mu)
    return A*np.exp(-fac/2)/N + offset

def fit_gaussian_form(X, A, x0, y0, sigma_x, sigma_y, p, offset):
    x, y = X
    return gaussian_2D(x, y, A, x0, y0, sigma_x, sigma_y, p, offset).flatten()

def fit_gaussian_2D(mot_img, background_file = None, p0 = [1, 0, 0, .2, .2, .005, 0], show_plot = False, show_resid = False, show_guess = False, c_max = None):
    ROI, mot_image = extract_ROI(mot_img, background_file)
    #mot_image = mot_image[:, :, 2] #extracting "blue" channel of png (though I think RGB all identical for this camera)

    y_pix, x_pix = mot_image.shape
    y_grid = np.linspace(-1, 1, y_pix)
    x_grid = np.linspace(-1, 1, x_pix)
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
        plt.contour(gaussian_2D(x, y, *vals), cmap = 'gray')

    if show_resid:
        plt.figure()
        plt.imshow(gaussian_2D(x, y, *vals) - mot_image, cmap = 'magma')
        plt.colorbar()    
        
    plt.show()
        
        #draw using opencv
    plt.gcf().canvas.draw()
    img = np.frombuffer(plt.gcf().canvas.tostring_rgb(), dtype =np.uint8)
    img = img.reshape(plt.gcf().canvas.get_width_height()[::-1] + (3, ))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imshow('fit_gaussian', img)
    plt.close()

def gaussian_1D(x, A, x0, sigma_x, offset):
    N =(sigma_x * np.sqrt(2 * np.pi))
    return A* np.exp(-(x - x0)**2/(2 * sigma_x**2))/N + offset

def fast_fit_gaussian(mot_img):
    '''
    Fit x, y axes independently, binning along each axis. From Toby's script
    '''
    mot_image = cv2.imread(mot_img[0], 0)
    y_data = np.sum(mot_image, axis = 1)
    x_data = np.sum(mot_image, axis = 0)
    y_pix, x_pix = mot_image.shape
    y_grid = np.linspace(-1, 1, y_pix)
    x_grid = np.linspace(-1, 1, x_pix)
    sigma_guess = .2
    p0_x = [(np.max(x_data) - np.min(x_data))*np.sqrt(2*np.pi)*sigma_guess, 0, sigma_guess, np.min(x_data)]
    p0_y = [(np.max(y_data) - np.min(y_data))*np.sqrt(2*np.pi)*sigma_guess, 0, sigma_guess, np.min(y_data)]
    x_bounds = ((-np.inf, -1, 0, -np.inf), (np.inf, 0, 50, np.inf))
    y_bounds = ((-np.inf, -1, 0, -np.inf), (np.inf, 1, 50, np.inf))
    try:
        x_vals, _ = curve_fit(gaussian_1D, x_grid, x_data, p0_x, bounds = x_bounds)
        y_vals, _ = curve_fit(gaussian_1D, y_grid, y_data, p0_y, bounds = y_bounds)


        X, Y = np.meshgrid(x_grid, y_grid)
        in_ellipse = ((X - x_vals[1])**2/x_vals[2]**2/4 + (Y - y_vals[1])**2/y_vals[2]**2/4) <= 1

        x0_plot = int((x_vals[1] + 1)*x_pix/2)
        y0_plot = int((y_vals[1] + 1)*y_pix/2)
        sigma_x_plot = int(x_vals[2]*x_pix/2)
        sigma_y_plot = int(y_vals[2]*y_pix/2)
        show_text = "X, Y 1/e**2: {:.2f} , {:.2f}".format(sigma_x_plot, sigma_y_plot)
        cv2.ellipse(mot_image, (x0_plot, y0_plot), (sigma_x_plot*2, sigma_y_plot*2), 0, 0, 360,(255, 105, 180), 5)

    except RuntimeError:
        show_text = "Fit not found"

    finally:
        cv2.putText(mot_image, show_text, (50, 850), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3) 
        cv2.imshow('gaussian', mot_image)
        print(x_vals[1], y_vals[1])



n_show = 30
#rough red mot
ROI_start = (400, 350)
ROI_end = (700, 600)

#rough blue mot
#ROI_start = (600, 250)
#ROI_end = (1000, 900) 
#ROI_start = (0, 0)
#sROI_end = (1200, 1200) 
live_data = np.full(n_show, None)

#cv2.namedWindow('align', cv2.WINDOW_NORMAL)
#cv2.namedWindow('align_plot', cv2.WINDOW_NORMAL)
#cv2.namedWindow('gaussian', cv2.WINDOW_NORMAL)
    
