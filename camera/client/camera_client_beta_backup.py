import sys, json, time, os
from shutil import copyfile
import numpy as np
from client_tools.connection3 import connection
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QToolBar, QFileDialog, QMenu, QLineEdit, QPushButton
from PyQt5.QtCore import QTimer, QDateTime
import data_analysis.imaging_tools as it
import warnings
from camera.client.live_plotter_client import LivePlotter
from twisted.internet.defer import inlineCallbacks

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

#from client_tools.connection import connection

class MplCanvas(FigureCanvas):
    def __init__(self):
        fig, ax = plt.subplots(1)
        self.fig = fig
        self.ax = ax

        self.fig.set_tight_layout(True)

        FigureCanvas.__init__(self, self.fig)
        self.setFixedSize(1200, 600)
        
class CameraGui(QtGui.QDialog):
    def set_class_vars(self):
        self.name = 'camera_gui'
        self.camera = 'No camera selected'
        self.file_to_show = None
        self.default_window_loc = 'C:/Users/srgang/labrad_tools/camera/client/windows/default_window.png'
        self.get_current_window_loc = lambda:'C:/Users/srgang/labrad_tools/camera/client/windows/current_window_{}.png'.format(self.camera)
        self.data_directory = 'K:/data/data'
        self.script = it.save_gui_window
        self.start_opt_widgets = 180
        self.ROI = [300, 400, 100, 100]
        self.show_title = True

        #For click events on image plot
        self.zoom = False
        self.pix = None
        self.img_xlim = None
        self.img_ylim = None

        #Rotation:
        self.rot = 0
        
        #For handling setting ROI with mouse
        self.listen_ROI = False
        self.first_click = True

        #Fluorescence imaging:
        self.background_file = None
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
        self.add_invisible_background_widgets()
        self.Plotter = LivePlotter(self)
        
        
        
#Main toolbar        
    def _create_toolbar(self):
        tools = self.menuBar()
        tools.addAction('Launch optimizer', self.launch)
        opts = tools.addMenu("&Options")
        file_opts = opts.addMenu('&File options')
        file_opts.addAction('Load file', self.load_image)
        file_opts.addAction('Save current screen', self.save_window)
        file_opts.addAction('Save current raw file', self.save_raw)
        view_opts = opts.addMenu('&View options')
        view_opts.addAction('Rotate counter-clockwise', self.rotate)
        view_opts.addAction('Reset rotation',  self.default_rot)
        view_opts.addAction('Toggle show title', self.toggle_title)
        view_opts.addAction('Background options', self.click_background_button)
        fitting = opts.addMenu('&Fitting options')
        fitting.addAction('None', self.none_action)
        fitting.addAction('ROI', self.ROI_action)
        fitting.addAction('2D Gaussian fit')
        cameras = opts.addMenu('&Camera')
        cameras.addAction('Horizontal MOT', self.set_horizontal_MOT)
        cameras.addAction('Vertical MOT', self.set_vertical_MOT)
        cameras.addAction('Cavity', self.set_cavity)
        cameras.addAction('Cavity perp', self.set_cavity_perp)
        
        

#View options
    def rotate(self):
        self.rot = (self.rot + 1)%4
        if self.rot != 0:
            self.ROI_zoom.setEnabled(False)
            for w in self.ROI_widgets[:-1]:
                w.setEnabled(False)
        else:
            self.ROI_zoom.setEnabled(True)
            for w in self.ROI_widgets[:-1]:
                w.setEnabled(True)
        self.show_window()
        
    def default_rot(self):
        self.rot = 0
        self.ROI_zoom.setEnabled(True)
        for w in self.ROI_widgets[:-1]:
            w.setEnabled(True)
        self.show_window()
        
    def toggle_title(self):
        self.show_title = not(self.show_title)
        self.show_window()

    def add_invisible_background_widgets(self):
        self.choose_background = QPushButton('Select background file', self)
        self.choose_background.setVisible(False)
        self.choose_background.setGeometry(self.start_opt_widgets + 110, 1, 350, 19)
        self.choose_background.clicked.connect(self.set_background)
        
        self.no_background = QPushButton('Clear background', self)
        self.no_background.setVisible(False)
        self.no_background.setEnabled(False)
        self.no_background.setGeometry(self.start_opt_widgets,1, 100, 19)
        self.no_background.clicked.connect(self.background_off)
        self.background_widgets = [self.choose_background, self.no_background]

    def click_background_button(self):
        self.remove_opt_widgets()
        for w in self.background_widgets:
            w.setVisible(True)
        
    def set_background(self):
        selected, filedialog = self.get_file_loc(mode = QFileDialog.AcceptOpen)
        if selected:
            path = str(filedialog.selectedFiles()[0])
            self.background_file = path
            prefix = "K:/data/data/"
            if path.startswith(prefix):
                short_path = path.removeprefix(prefix)
            else:
                short_path = path
            self.choose_background.setText("Background: " + short_path)
            self.no_background.setEnabled(True)
            self.show_window()
                  
    def background_off(self):
        self.background_file = None
        self.choose_background.setText('Select background file')
        self.no_background.setEnabled(False)
        
#file options
    def get_file_loc(self, mode = QFileDialog.AcceptSave):
        filedialog = QFileDialog(self)
        filedialog.setDefaultSuffix("png")
        time_string = time.strftime('%Y%m%d')
        filedialog.setDirectory(os.path.join(self.data_directory, time_string))
        filedialog.setAcceptMode(mode)
        selected = filedialog.exec()
        return selected, filedialog
    
    def load_image(self):
        selected, filedialog = self.get_file_loc(mode = QFileDialog.AcceptOpen)
        if selected:
            path = str(filedialog.selectedFiles()[0])
            self.camera = 'Load file'
            self.file_to_show = path
            if "horizontal_mot" in path:
                self.pix = [964, 1292]#[68, 160]
                self.img_xlim = [100, 515]
                self.img_ylim = [75, 635]
                self.sketchy_subtract = 0
            else:
                self.pix = [1216, 1936]
                self.img_xlim = [90, 520]
                self.img_ylim = [80, 770]
                self.sketchy_subtract = 100
                
                
            self.show_window()
        
    def save_raw(self):
        selected, filedialog = self.get_file_loc()
        if selected:
            path = str(filedialog.selectedFiles()[0])
            copyfile(self.file_to_show, path)

    def save_window(self):
        selected, filedialog = self.get_file_loc()
        if selected:
            path = str(filedialog.selectedFiles()[0])
            copyfile(self.get_current_window_loc(), path)
        
            
#Selecting camera
    def set_horizontal_MOT(self):
        self.camera = 'horizontal_mot'
        self.pix = [964, 1292]#[68, 160]## #
        self.img_xlim = [100, 515]
        self.img_ylim = [75, 635]
        self.sketchy_subtract = 0
        self.show_window()

    def set_vertical_MOT(self):
        self.camera = 'vertical_mot'
        self.pix = [1216, 1936]
        self.img_xlim = [90, 520]
        self.img_ylim = [80, 770]
        self.sketchy_subtract = 100 #mysterious fudge factor to make clicks align with reality ...
        self.show_window()

    def set_cavity(self):
        self.camera = 'cavity'
        self.pix = [1216, 1936]
        self.img_xlim = [90, 520]
        self.img_ylim = [80, 770]
        self.sketchy_subtract = 100 #mysterious fudge factor to make clicks align with reality ...
        self.show_window()

    def set_cavity_perp(self):
        self.camera = 'cav_perp'
        self.pix = [964, 1292]
        self.img_xlim = [100, 515]
        self.img_ylim = [75, 635]
        self.sketchy_subtract = 0
        self.show_window()

#Everything ROI-related     
    def add_invisible_ROI_widgets(self):
        self.xROI = QLineEdit(self)
        self.yROI = QLineEdit(self)
        self.widthROI = QLineEdit(self)
        self.heightROI = QLineEdit(self)
        self.ROI_click_button = QPushButton('Set ROI with mouse', self)
        self.ROI_click_button.setVisible(False)
        click_button_width = 120
        num_width = 40
        spacer = 9
        self.ROI_click_button.setGeometry(self.start_opt_widgets, 1, click_button_width, 19)
        self.ROI_click_button.clicked.connect(self.handle_ROI_click_button)
        self.ROI_zoom = QPushButton('Zoom to ROI', self)
        self.ROI_zoom.setVisible(False)
        self.ROI_zoom.setGeometry(self.start_opt_widgets + click_button_width + spacer +4*(num_width + spacer),1, 100, 19)
        self.ROI_zoom.clicked.connect(self.zoom_to_ROI)
        self.ROI_widgets = [self.xROI, self.yROI, self.widthROI, self.heightROI, self.ROI_click_button, self.ROI_zoom]
        for i in np.arange(len(self.ROI_widgets) - 2):
            w = self.ROI_widgets[i]
            w.setGeometry(self.start_opt_widgets + click_button_width + spacer*(i + 1) + num_width*i, 1, num_width, 19)
            w.returnPressed.connect(self.update_ROI(i))
            w.setVisible(False)

    def zoom_to_ROI(self):
        self.zoom = not(self.zoom)
        if self.zoom:
            self.ROI_zoom.setText('Un-zoom')
            for w in self.ROI_widgets[:-1]:
                w.setEnabled(False)
        else:
            self.ROI_zoom.setText('Zoom to ROI')
            for w in self.ROI_widgets[:-1]:
                w.setEnabled(True)
        self.show_window()
        
    def update_ROI_text(self):
        for i in np.arange(len(self.ROI_widgets) - 2):
            self.ROI_widgets[i].setText(str(self.ROI[i]))
            
    def remove_opt_widgets(self):
        for w in self.ROI_widgets:
            w.setVisible(False)
        for w in self.background_widgets:
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
            self.x_scale = self.pix[0]/(self.img_xlim[1] - self.img_xlim[0])
            self.y_scale = self.pix[1]/(self.img_ylim[1] - self.img_xlim[0])
            x_img = int((event.pos().x() - self.img_xlim[0])*self.x_scale)
            y_img = int((self.img_ylim[1] - event.pos().y())*self.y_scale) + self.sketchy_subtract
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
        self.remove_opt_widgets()
        for w in self.ROI_widgets:
            w.setVisible(True)
        self.update_ROI_text()
        self.script = it.save_gui_window_ROI
        self.Plotter.script = self.Plotter.ROI_counts 
        self.show_window()

#When none option clicked,
    def none_action(self):
        self.script = it.save_gui_window
        self.Plotter.script = self.Plotter.total_counts
        self.remove_opt_widgets()
        self.show_window()
        
    def call_visualization_fxn(self, title):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            _ = self.script(self.file_to_show, self.get_current_window_loc(), self.ROI, self.rot, self.show_title, title, self.zoom, self.background_file)

#Launch live_plotter
    def launch(self):
        self.Plotter.show()

#Repaint function:  
    def show_window(self):
        self.title = "{}: {}".format(self.camera, self.file_to_show)
        self.setWindowTitle(self.title)
        label = QLabel(self)
        try:
            if self.file_to_show is not None:
                title = self.Plotter.script()
                self.call_visualization_fxn(title)
                pixmap = QPixmap(self.get_current_window_loc())
            else:
                pixmap = QPixmap(self.default_window_loc)
            label.setPixmap(pixmap)
            self.setCentralWidget(label)
            self.resize(pixmap.width(), pixmap.height())
            label.mousePressEvent = self.handle_click
        except AttributeError:
            print('Not loaded')

#Labrad connection:
    @inlineCallbacks    
    def connect_to_labrad(self):
        #self.cxn = connect(name=self.name)
        self.cxn = connection()
        yield self.cxn.connect(name = 'camera viewer')
        server = yield self.cxn.get_server('camera')
        yield server.signal__update(self.update_id)
        yield server.addListener(listener = self.receive_update, source=None, ID=self.update_id)
        print('connected')
        
    def receive_update(self, c, update_json):
        update = json.loads(update_json)
        for key, value in update.items():
            if key == self.camera:
                if self.fluorescence_mode:
                    if not (('exc' in value[0]) or ('background' in value[0])):
                        str_end = '_fluorescence.png'
                        keyword = 'fluor_'
                        split_str = value[0].partition(str_end)
                        parse_name = split_str[0].partition(keyword)
                        beginning = parse_name[0]
                        shot_num = int(parse_name[-1])
                        offset = 3
                        mod_shot = shot_num - offset
                        new_path = beginning + keyword + str(mod_shot) + str_end
                        print(value)
                        print(new_path)
                        
                        self.file_to_show = new_path#value[0]
                        self.show_window()
                        self.Plotter.show_window()
                    


