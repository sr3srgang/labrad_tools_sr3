'''
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    import qt5reactor
    qt5reactor.install()
    w = CameraGui()
    w.show()
    sys.exit(app.exec_())
'''

import sys, json, time
import numpy as np
from client_tools.connection3 import connection
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QToolBar, QMenu, QLineEdit, QPushButton
from PyQt5.QtCore import QTimer, QDateTime
import data_analysis.imaging_tools as it
import warnings
from camera.live_plotter_client import LivePlotter
from twisted.internet.defer import inlineCallbacks


class CameraGui(QMainWindow):
    def set_class_vars(self):
        self.name = 'camera_gui'
        self.camera = 'horizontal_mot'
        self.file_to_show = None
        self.default_window_loc = 'C:/Users/srgang/labrad_tools/camera/default_window.png'
        self.current_window_loc = 'C:/Users/srgang/labrad_tools/camera/current_window.png'
        self.script = it.save_gui_window
        self.start_opt_widgets = 275
        self.ROI = [300, 400, 100, 100]

        #For click events on image plot
        self.img_xlim = [100, 530]
        self.img_ylim = [120, 710]
        self.x_scale = 964/(self.img_xlim[1] - self.img_xlim[0])
        self.y_scale = 1292/(self.img_ylim[1] - self.img_xlim[0])

        #For handling setting ROI with mouse
        self.listen_ROI = False
        self.first_click = True

        self.fluorescence_mode = True
    
    def __init__(self):
        super(CameraGui, self).__init__()
        
        self.set_class_vars()
        #Labrad connection:
        self.update_id = np.random.randint(0, 2**31 - 1)
        self.connect_to_labrad()
        
        #Set up window
        self.show_window()
        self._create_toolbar()
        self.add_invisible_ROI_widgets()
        self.Plotter = LivePlotter(self)
        
        
        
#Main toolbar        
    def _create_toolbar(self):
        tools = self.menuBar()
        tools.addAction('Launch optimizer', self.launch)
        tools.addAction('Load file', self.show_window)

        opts = tools.addMenu("&Options")
        fitting = opts.addMenu('&Fitting options')
        fitting.addAction('None', self.none_action)
        fitting.addAction('ROI', self.ROI_action)
        fitting.addAction('2D Gaussian fit')
        cameras = opts.addMenu('&Camera')
        cameras.addAction('Horizontal MOT')
        cameras.addAction('Vertical MOT')

#Everything ROI-related     
    def add_invisible_ROI_widgets(self):
        self.xROI = QLineEdit(self)
        self.yROI = QLineEdit(self)
        self.widthROI = QLineEdit(self)
        self.heightROI = QLineEdit(self)
        self.ROI_click_button = QPushButton('Set ROI with mouse', self)
        self.ROI_click_button.setVisible(False)
        click_button_width = 120
        num_width = 45
        spacer = 10
        self.ROI_click_button.setGeometry(self.start_opt_widgets, 1, click_button_width, 19)
        self.ROI_click_button.clicked.connect(self.handle_ROI_click_button)
        self.ROI_widgets = [self.xROI, self.yROI, self.widthROI, self.heightROI, self.ROI_click_button]
        for i in np.arange(len(self.ROI_widgets) - 1):
            w = self.ROI_widgets[i]
            w.setGeometry(self.start_opt_widgets + click_button_width + spacer*(i + 1) + num_width*i, 1, num_width, 19)
            w.returnPressed.connect(self.update_ROI(i))
            w.setVisible(False)
            
    def update_ROI_text(self):
        for i in np.arange(len(self.ROI_widgets) - 1):
            self.ROI_widgets[i].setText(str(self.ROI[i]))
            
    def remove_opt_widgets(self):
        for w in self.ROI_widgets:
            w.setVisible(False)
        
    def update_ROI(self, i):
        def wrapped_update_ROI():
            self.ROI[i] = int(self.ROI_widgets[i].text())
            self.show_window()
        return wrapped_update_ROI

    def handle_ROI_click_button(self):
        self.listen_ROI = True
        self.first_click = True

    def handle_click(self, event):
        if self.listen_ROI:
            x_img = int((event.pos().x() - self.img_xlim[0])*self.x_scale)
            y_img = int((self.img_ylim[1] - event.pos().y())*self.y_scale)
            if self.first_click:
                self.ROI[0] = x_img
                self.ROI[1] = y_img
                self.first_click = False
            else:
                self.ROI[2] = x_img - self.ROI[0]
                self.ROI[3] = y_img - self.ROI[1]
                self.first_click = True
                self.listen_ROI = False
                self.show_window()
            self.update_ROI_text()
        
    def ROI_action(self):
        for w in self.ROI_widgets:
            w.setVisible(True)
        self.update_ROI_text()
        self.script = lambda mot_img, save_loc: it.save_gui_window_ROI(mot_img, save_loc, self.ROI)
        self.Plotter.script = self.Plotter.ROI_counts 
        self.show_window()

#When none option clicked,
    def none_action(self):
        self.script = it.save_gui_window
        self.Plotter.script = self.Plotter.total_counts
        self.remove_opt_widgets()
        self.show_window()
        
    def call_visualization_fxn(self):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            fig = self.script(self.file_to_show, self.current_window_loc)


#Launch live_plotter
    def launch(self):
        self.Plotter.show()

#Repaint function:  
    def show_window(self):
        self.title = self.camera
        self.setWindowTitle(self.title)
        label = QLabel(self)
        if self.file_to_show is not None:
            self.call_visualization_fxn()
            pixmap = QPixmap(self.current_window_loc)
        else:
            pixmap = QPixmap(self.default_window_loc)
        label.setPixmap(pixmap)
        self.setCentralWidget(label)
        self.resize(pixmap.width(), pixmap.height())
        label.mousePressEvent = self.handle_click

#Labrad connection:
    @inlineCallbacks    
    def connect_to_labrad(self):
        #self.cxn = connect(name=self.name)
        self.cxn = connection()
        yield self.cxn.connect(name = 'camera viewer')
        server = yield self.cxn.get_server('conductor')
        yield server.signal__update(self.update_id)
        yield server.addListener(listener = self.receive_update, source=None, ID=self.update_id)
        
    def receive_update(self, c, update_json):
        update = json.loads(update_json)
        for key, value in update.items():
            if key == 'horizontal_mot':
                if self.fluorescence_mode:
                    self.file_to_show = value[0]
                    time.sleep(.1)
                    self.show_window()
                    self.Plotter.show_window()
                    


