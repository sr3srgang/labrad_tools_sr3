import os, glob, time, matplotlib, cv2
import numpy as np
import matplotlib.pyplot as plt
from pylab import imread

def get_most_recent_file(directory, ext = '.png'):
    files = glob.glob(directory + "/*" + ext)
    try:
        return max(files, key = os.path.getctime)
    except:
        pass

def auto_refresh_dir(directory, script, ext = '.png', refresh_time = .1):
    while True:
        try:
            file = get_most_recent_file(directory, ext)
            script(file)
            cv2.waitKey(100)
        except KeyboardInterrupt:
            break
        except:
           # print('oops!')
            pass

def align_mot(img, background_file = None):
    mot_image = imread(img)
    if background_file is not None:
        background = imread(background_file)
        mot_image -= background
    show_text = "{:.2f}*1e+5".format(np.sum(mot_image*1e-5))
    cv2.putText(mot_image, show_text, (200, 150), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 255, 255), 3) 
    cv2.imshow('align', mot_image)

auto_refresh_dir('K:/data/data/20210116/**', align_mot)
    
