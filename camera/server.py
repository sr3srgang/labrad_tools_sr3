
from labrad.server import LabradServer
from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor, task
import cv2
import numpy as np

from labrad.server import setting
from vimba import *

class CameraServer(LabradServer):
    """Mako camera server using Vimba Python3 API
    """

    name = 'zuko_camera'
    this_camera = None


    @setting(0)
    def init_camera(self, c):
        with Vimba.get_instance() as vimba:
            all_cam = vimba.get_all_cameras()
            cam = all_cam[0]
            self.this_camera = cam
            print(cam)

            with cam:
                cam.TriggerSource.set('Line1')
                cam.TriggerSelector.set('FrameStart')
                cam.TriggerMode.set('On')
                cam.AcquisitionMode.set('Continuous')

    @setting(1)
    def get_frame(self, c, camera_save_path):
        with Vimba.get_instance() as vimba:
            cam = self.this_camera
            with cam:
                frame = cam.get_frame(5000)
                print('Frame acquired: ' + camera_save_path)
                img = frame.as_opencv_image()[:,:, 0]
                #cv2.imwrite(camera_save_path, frame.as_opencv_image())
                np.savetxt(camera_save_path, img)
    @setting(2)
    def say_hello(self, c):
        print('hizukohere')


    


# create an instance of our server class
__server__ = CameraServer()

# this is some boilerplate code to run the
# server when this module is executed
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
