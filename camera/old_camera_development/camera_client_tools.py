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

def live_plot_ROI(img, ROI, data):
    mot_image = cv2.imread(img, 0).T.astype(np.int16)
    roi_vals = mot_image[ROI[0]:ROI[0] + ROI[3], ROI[1]:ROI[1]+ROI[3]]
    this_shot = np.sum(ROI)

    empty_data = np.where(data == None)
    
                                            
                                            
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
    
live_data = np.full(n_show, None)

    
