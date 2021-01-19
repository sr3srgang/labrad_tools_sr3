import os, glob, time, matplotlib, cv2
import numpy as np
import matplotlib.pyplot as plt
from pylab import imread

def get_today_path():
    time_string = time.strftime('%Y%m%d')
    return 'K:/data/data/' + time_string + '/**'

def get_most_recent_file(directory, ext = '.png'):
    files = glob.glob(directory + "/*" + ext, recursive = True)
    try:
        return max(files, key = os.path.getmtime)
    except:
        pass

def auto_refresh_dir(script, ext = '.png', refresh_time = 1):
    while True:
        try:
            this_dir = get_today_path()
            file = get_most_recent_file(this_dir, ext)
            script(file)
            cv2.waitKey(refresh_time*1000)
        except TypeError:
            pass
        except SyntaxError:
            pass
        except KeyboardInterrupt:
            break

def align_mot(img, background_file = None):
    mot_image = imread(img)
    if background_file is not None:
        background = imread(background_file)
        mot_image -= background
    show_text = "{:.2f}*1e+4".format(np.sum(mot_image*1e-4))
    cv2.putText(mot_image, show_text, (200, 150), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 255, 255), 3) 
    cv2.imshow('align', mot_image)

def align_mot_ROI(img, background_file = None):
    mot_image = imread(img)
    if background_file is not None:
        background = imread(background_file)
        mot_image -= background
    x0, y0 = ROI_start
    xf, yf = ROI_end
    ROI = mot_image[x0:xf, y0:yf]
    show_text = "{:.2f}*1e+3".format(np.sum(ROI*1e-3))
    cv2.putText(mot_image, show_text, (200, 150), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 255, 255), 3) 
    cv2.rectangle(mot_image, ROI_start, ROI_end, (255, 105, 180), 1)
    cv2.imshow('align', mot_image)

def live_plot_ROI(img, background_file = None):
    mot_image = imread(img)
    if background_file is not None:
        background = imread(background_file)
        mot_image -= background
    x0, y0 = ROI_start
    xf, yf = ROI_end
    ROI = mot_image[x0:xf, y0:yf]
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
   # plt.ylim(25, 27)
    plt.gcf().canvas.draw()
    img = np.frombuffer(plt.gcf().canvas.tostring_rgb(), dtype =np.uint8)
    img = img.reshape(plt.gcf().canvas.get_width_height()[::-1] + (3, ))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imshow('align_plot', img)
    plt.close()

    

n_show = 30
ROI_start = (400, 50)
ROI_end = (1000, 800) 
live_data = np.full(n_show, None)
    
