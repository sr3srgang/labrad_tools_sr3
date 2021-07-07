import sys, json, time, os
from shutil import copyfile
import numpy as np
from client_tools.connection3 import connection
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QDialog,QGridLayout
from PyQt5.QtCore import QTimer, QDateTime
import data_analysis.imaging_tools as it
import warnings
from camera.client.live_plotter_client_beta import LivePlotter
from twisted.internet.defer import inlineCallbacks

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
#from client_tools.connection import connection

class MplCanvas(FigureCanvas):
    def __init__(self):
        fig, ax = plt.subplots(1)
        self.fig = fig
        self.fig.set_facecolor('k')
        self.ax = ax

        self.fig.set_tight_layout(True)

        FigureCanvas.__init__(self, self.fig)
        self.setFixedSize(600, 800)

class CameraGui(QDialog):
    def set_vars(self):
        self.camera = 'horizontal_mot'
        self.name = self.camera
        self.fluorescence_mode = True
        self.update_id = np.random.randint(0, 2**31 - 1)
        self.ROI = None
        self.no_lim = True
    
    def __init__(self):
        super(CameraGui, self).__init__(None)
        self.set_vars()
        self.connect_to_labrad()
        self.populate()
        self.Plotter = LivePlotter(self)
        

    def populate(self):
        self.setWindowTitle(self.name)
        self.canvas = MplCanvas()
        
        self.nav = NavigationToolbar(self.canvas, self)
        self.nav.addAction('Select analysis method')
        self.nav.addAction('Launch live plotter', self.launch_plotter)
          
        self.layout = QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.layout.addWidget(self.nav)
        self.layout.addWidget(self.canvas)

        self.setLayout(self.layout)
        width = self.canvas.width()
        height = self.nav.height() + self.canvas.height()
        self.setFixedSize(width, height)
        
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
                        print(value)
                        if 'gnd' in value[0]:
                            str_end = '_fluorescence.png'
                            keyword = 'fluor_'
                            split_str = value[0].partition(str_end)
                            parse_name = split_str[0].partition(keyword)
                            beginning = parse_name[0]
                            shot_num = int(parse_name[-1])
                            offset = 3
                            mod_shot = shot_num - offset
                            new_path = beginning + keyword + str(mod_shot) + str_end
                            print(new_path)
                            self.file_to_show = new_path#value[0]
                        else:
                            self.file_to_show = value[0]

                        self.Plotter.show_window()
                        self.show_window()
                        

    def show_window(self):
        if not self.no_lim:
            xlim = self.canvas.ax.get_xlim()
            ylim = self.canvas.ax.get_ylim()    
        self.canvas.ax.clear()
        it.fig_gui_window_ROI(self.file_to_show, self.canvas.ax, self.ROI)
        if not self.no_lim:
            self.canvas.ax.set_xlim(xlim)
            self.canvas.ax.set_ylim(ylim)
        else:
            self.no_lim = False
        print(self.canvas.ax.get_xlim())
        self.canvas.ax.set_title("{:.3e}".format(self.Plotter.title), color = 'w', y = .85, size = 42)
        self.canvas.draw()
        print('redrawn')
        
    def launch_plotter(self):
        self.Plotter.show()
