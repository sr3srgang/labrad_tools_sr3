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

def auto_refresh_dir(script, ext = '.png', refresh_time = .1):
    while True:
        try:
            this_dir = get_today_path()
            file = get_most_recent_file(this_dir, ext)
            script(file)
            cv2.waitKey(1000)
        except KeyboardInterrupt:
            break
        except:
            pass

def align_mot(img, background_file = None):
    mot_image = imread(img)
    if background_file is not None:
        background = imread(background_file)
        mot_image -= background
    show_text = "{:.2f}*1e+5".format(np.sum(mot_image*1e-5))
    cv2.putText(mot_image, show_text, (200, 150), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 255, 255), 3) 
    cv2.imshow('align', mot_image)

auto_refresh_dir(align_mot)
    
