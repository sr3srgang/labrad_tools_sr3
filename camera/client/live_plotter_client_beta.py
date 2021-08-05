import sys, json, time, os
from shutil import copyfile
import numpy as np
from client_tools.connection3 import connection
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QDialog,QGridLayout
from PyQt5.QtCore import QTimer, QDateTime
import data_analysis.imaging_tools as it
import warnings
from twisted.internet.defer import inlineCallbacks

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class MplCanvas(FigureCanvas):
    def __init__(self):
        fig, ax = plt.subplots(1)
        self.fig = fig
        self.ax = ax

        self.fig.set_tight_layout(True)

        FigureCanvas.__init__(self, self.fig)
        self.setFixedSize(600, 300)

class LivePlotter(QDialog):
	
	def set_class_vars(self):
		self.script = it.fig_plotter
		self.n_show = 30
		self.live_data = np.full(self.n_show, None)
	
	def __init__(self, parent):
		super(LivePlotter, self).__init__()
		self.parent = parent
		self.set_class_vars()
		self.populate()

	def populate(self):
		self.setWindowTitle('Live plotter')
		self.canvas = MplCanvas()
		self.nav = NavigationToolbar(self.canvas, self)
		'''Changed nav toolbar'''
		self.nav.addAction('Reset optimizer', self.reset_opt)
		
		self.layout = QGridLayout()
		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0, 0, 0, 0)
		
		self.layout.addWidget(self.nav)
		self.layout.addWidget(self.canvas)

		self.setLayout(self.layout)
		#self.canvas.ax.set_ylim((0, 5e-5))
		#self.canvas.ax.set_xlim((0, .04))
		width = self.canvas.width()
		height = self.nav.height() + self.canvas.height() + 20
		self.setFixedSize(width, height)


	def reset_opt(self):
		self.live_data = np.full(self.n_show, None)
	
	def live_plot(self):
		#try:
		    roi = self.get_ROI()
		    this_shot = self.script(self.parent.file_to_show, roi)
		    self.title = this_shot
		    empty_data = np.where(self.live_data == None)
		    if len(empty_data[0]) == 0:
		        self.live_data[0:self.n_show - 1] = self.live_data[1:self.n_show]
		        self.live_data[-1] = this_shot
		    else:
		        self.live_data[empty_data[0][0]] = this_shot
		#except AttributeError:
		 #   print('Not loaded')

	def get_ROI(self):
            xlim = self.parent.canvas.ax.get_xlim()
            ylim = self.parent.canvas.ax.get_ylim()
            ROI_exact = [xlim[0], ylim[0], xlim[1] - xlim[0], ylim[1] - ylim[0]]
            return [int(x) for x in ROI_exact]
            
            
	def show_window(self):
		self.live_plot()
		self.canvas.ax.clear()
		self.canvas.ax.plot(self.live_data, 'o')
		#self.canvas.ax.title(np.std(self.live_data))
		self.canvas.draw()
		
