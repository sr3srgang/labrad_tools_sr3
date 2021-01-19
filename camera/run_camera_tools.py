from camera_tools import *
import cv2

test_img = 'K:/images/1_14_TOF_2/cam_img_01_14_2021_13_50_54_114654.png'
background = 'K:/images/1_14_TOF_2/cam_img_01_14_2021_13_50_56_787585.png'
#fit_gaussian_2D(test_img, background_file = background, show_plot = True, c_max = 1)
#cv2.waitKey(0)#print(vals)

#auto_refresh_dir(fast_fit_gaussian)
def combined(img):
    align_mot_ROI(img)
    fast_fit_gaussian(img)
    live_plot_ROI(img)    

auto_refresh_dir(combined)
