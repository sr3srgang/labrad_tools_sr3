from vimba import *
import cv2, time
import numpy as np
import sys, json
import numpy as np
from labrad import connect
from client_tools.connection3 import connection
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QToolBar, QMenu, QLineEdit, QPushButton
from PyQt5.QtCore import QTimer, QDateTime, QObject, QThread, pyqtSlot
import data_analysis.imaging_tools as it
import warnings
from camera.live_plotter_client import LivePlotter
from twisted.internet.defer import inlineCallbacks
from queue import Queue

class Stream(QObject):
    def __init__(self, cam):
        super(Stream, self).__init__()
        self.cam = cam
        self.paths = Queue()
        self.waiting = False
        
    @pyqtSlot()
    def start_stream(self):
        with Vimba.get_instance() as vimba:
            cam = self.cam
            with cam:
                try:
                    cam.start_streaming(self.handler)
                    while True:
                        time.sleep(1)
                finally:
                    cam.stop_streaming()
                    
    def handler(self, cam, frame):
        print('Frame acquired')
        cam.queue_frame(frame)
        this_path = self.paths.get_nowait()
        cv2.imwrite(this_path, frame.as_opencv_image())
        print(this_path)

        

class Camera(QMainWindow):
    
    def __init__(self):
        super(Camera, self).__init__()
        self.camera_names = ['horizontal_mot', 'vertical_mot']
        self.init_cameras()
        self.update_id = np.random.randint(0, 2**31 - 1)
        self.connect_to_labrad()

        #Starting async thread for camera stream
        self.stream = self.start_streaming(self.this_camera)
            
    #Labrad connection:
    @inlineCallbacks    
    def connect_to_labrad(self):
        #self.cxn = connect(name=self.name)
        self.cxn = connection()
        yield self.cxn.connect(name = 'camera')
        server = yield self.cxn.get_server('conductor')
        yield server.signal__update(self.update_id)
        yield server.addListener(listener = self.receive_update, source=None, ID=self.update_id)
        
    def receive_update(self, c, update_json):
        update = json.loads(update_json)
        for key, value in update.items():
            if key == 'horizontal_mot':
                for path in value:
                    self.stream.paths.put_nowait(path)

    def init_cameras(self):
        with Vimba.get_instance() as vimba:
            all_cam = vimba.get_all_cameras()
            cam = all_cam[0]
            self.this_camera = cam
            
            with cam:
                cam.TriggerSource.set('Line1')
                cam.TriggerActivation.set('RisingEdge')
                cam.TriggerSelector.set('FrameStart')
                cam.TriggerMode.set('On')
                cam.AcquisitionMode.set('Continuous')
                cam.ExposureMode.set('TriggerWidth')
                cam.Gain.set(30)

    def start_streaming(self, cam):
        stream = Stream(self.this_camera)
        self.thread = QThread(self)
        stream.moveToThread(self.thread)
        self.thread.started.connect(stream.start_stream)
        self.thread.start()
        return stream
        
    def set_gain(self, c, gain_val):
        with Vimba.get_instance() as vimba:
            cam = self.this_camera
            with cam:
                cam.Gain.set(gain_val)
