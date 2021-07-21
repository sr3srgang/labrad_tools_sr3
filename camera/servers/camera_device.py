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
from twisted.internet.defer import inlineCallbacks
from queue import Queue

class Stream(QObject):
    def __init__(self, cam, cam_name, cxn):
        super(Stream, self).__init__()
        self.cam = cam
        self.cam_name = cam_name
        self.paths = Queue()
        self.cxn = cxn
        
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
        print('Frame acquired: ' + self.cam_name)
        cam.queue_frame(frame)
        if not self.paths.empty():
            this_path = self.paths.get_nowait()
            cv2.imwrite(this_path, frame.as_opencv_image())
            print(this_path)
            #self.cxn.camera._send_update({self.cam + '_display': [this_path]})


        

class Camera(QMainWindow):
    
    def __init__(self, cam_name, cam_id):
        super(Camera, self).__init__()
        self.cam_name = cam_name
        #Used to set camera to whatever gain should be when it comes online:
        self.gain_name = cam_name + '_gain'
        self.at_init = True
        self.default_gain = 40
        
        self.update_gain_name = 'update_' + cam_name + '_gain'
        self.cam_id = cam_id
        self.update_id = np.random.randint(0, 2**31 - 1)
        self.connect_to_labrad()
        self.init_camera()
        
        #Starting async thread for camera stream
        self.stream = self.start_streaming()
            
    #Labrad connection:
    @inlineCallbacks    
    def connect_to_labrad(self):
        #self.cxn = connect(name=self.name)
        self.cxn = connection()
        yield self.cxn.connect(name = 'camera')
        print('connected to labrad')
        server = yield self.cxn.get_server('camera')
        print('got camera server')
        yield server.signal__update(self.update_id)
        yield server.addListener(listener = self.receive_update, source=None, ID=self.update_id)
        print('connected!')
        
    def receive_update(self, c, update_json):
        update = json.loads(update_json)
        print(update)
        for key, value in update.items():
            if key == self.cam_name:
                for path in value:
                    self.stream.paths.put_nowait(path)
            if key == self.update_gain_name:
                print('UPDATE')
                print(key, value)
                self.set_gain(int(value))
            if key == self.gain_name:
                if self.at_init:
                    print(key, value)
                    if value is None:
                        value = 40
                    self.set_gain(int(value))
                    self.at_init = False
        
    def init_camera(self):
        with Vimba.get_instance() as vimba:
            all_cam = vimba.get_all_cameras()
            print(all_cam)
            found_cam = False
            for cam in all_cam:
                if cam.get_id() == self.cam_id:
                    found_cam = True
                    break
            if not found_cam:
                raise ValueError('Camera not found!!')
            self.this_camera = cam
            print(self.this_camera.get_id())
            
            with cam:
                cam.TriggerSource.set('Line1')
                cam.TriggerActivation.set('RisingEdge')
                cam.TriggerSelector.set('FrameStart')
                cam.TriggerMode.set('On')
                cam.AcquisitionMode.set('Continuous')
                cam.ExposureMode.set('TriggerWidth')

    def start_streaming(self):
        stream = Stream(self.this_camera, self.cam_name, self.cxn)
        self.thread = QThread(self)
        stream.moveToThread(self.thread)
        self.thread.started.connect(stream.start_stream)
        self.thread.start()
        return stream
        
    def set_gain(self, gain_val):
        with Vimba.get_instance() as vimba:
            cam = self.this_camera
            with cam:
                cam.Gain.set(gain_val)
