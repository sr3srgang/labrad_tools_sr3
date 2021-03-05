import sys, cv2
import numpy as np
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QToolBar, QMenu, QLineEdit, QPushButton
from PyQt5.QtCore import QTimer, QDateTime
import data_analysis.imaging_tools as it
import warnings
import matplotlib.pyplot as plt


class LivePlotter(QMainWindow):
    def set_class_vars(self):
        self.script = self.total_counts
        self.n_show = 30
        self.live_data = np.full(self.n_show, None)
        self.current_window_loc = 'C:/Users/srgang/labrad_tools/camera/client/windows/current_plotter_window.png'

        
    def __init__(self, parent):
        super(LivePlotter, self).__init__()
        self.parent = parent
        self.set_class_vars()
        self.add_menu()

    def add_menu(self):
        tools = self.menuBar()
        tools.addAction('Reset optimizer', self.reset_opt)

    def reset_opt(self):
        self.live_data = np.full(self.n_show, None)

    def total_counts(self):
        mot_image = it.process_file(self.parent.file_to_show, background = self.parent.background_file)
        return np.sum(mot_image)

    def ROI_counts(self):
        mot_image = it.process_file(self.parent.file_to_show, zoom = True, ROI = self.parent.ROI, background = self.parent.background_file)
        mot_image = cv2.imread(self.parent.file_to_show, 0).T.astype(np.int16)
        x0 = self.parent.ROI[0]
        y0 = self.parent.ROI[1]
        return np.sum(mot_image[y0:y0+self.parent.ROI[3], x0:x0 + self.parent.ROI[2]])
                      
    def live_plot(self):
        this_shot = self.script()
        empty_data = np.where(self.live_data == None)
        if len(empty_data[0]) == 0:
            self.live_data[0:self.n_show - 1] = self.live_data[1:self.n_show]
            self.live_data[-1] = this_shot
        else:
            self.live_data[empty_data[0][0]] = this_shot

    def make_plot(self):
        fig = plt.figure()
        plt.plot(self.live_data, 'o-k')
        plt.xlim((-1, self.n_show))
        fig.savefig(self.current_window_loc)
        plt.close()

    def show_window(self):
        self.live_plot()
        self.make_plot()
        self.title = "Live plotter"
        self.setWindowTitle(self.title)
        label = QLabel(self)
        pixmap = QPixmap(self.current_window_loc)
        label.setPixmap(pixmap)
        self.setCentralWidget(label)
        self.resize(pixmap.width(), pixmap.height())
        
        
            
        
             
        
        
        
