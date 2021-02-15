from camera_tools import *

test_file = 'K:/images/1_14_TOF_2/cam_img_01_14_2021_13_51_51_248690.png'

def together(img):
   # align_mot(img)
    align_mot_ROI(img)
    live_plot_ROI_shot(img)
   # fast_fit_gaussian(img)
    #fit_gaussian_2D(img, show_plot = True)
most_recent_file = None
auto_refresh_dir(together)
