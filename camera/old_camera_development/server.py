
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

    def initServer(self):
        from camera.camera_device import Camera
        self.cam = Camera()
   
    @setting(3)
    def say_hello(self, c):
        print('hizukohere')


    

'''
# create an instance of our server class
__server__ = CameraServer()

# this is some boilerplate code to run the
# server when this module is executed
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
'''
