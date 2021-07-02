import json
import h5py
import os
from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks, returnValue
import numpy as np
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from data_analysis.pico import ones
from client_tools.connection import connection

class MplCanvas(FigureCanvas):
    def __init__(self):
        fig, ax = plt.subplots(1)
        self.fig = fig
        self.ax = ax

        self.fig.set_tight_layout(True)

        FigureCanvas.__init__(self, self.fig)
        self.setFixedSize(600, 300)

class PicoPlotter(QtGui.QDialog):
	
	def set_class_vars(self):
		self.script = ones
		self.n_show = 30
		self.live_data = np.full(self.n_show, None)
	
	def __init__(self, parent):
		super(PicoPlotter, self).__init__()
		self.parent = parent
		self.set_class_vars()
		self.populate()
		
    	def populate(self):
		self.setWindowTitle('Live plotter')
		self.canvas = MplCanvas()
		self.nav = NavigationToolbar(self.canvas, self)
		'''Changed nav toolbar'''
		self.nav.addAction('Reset optimizer', self.reset_opt)
		
		self.layout = QtGui.QGridLayout()
		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0, 0, 0, 0)
		
		self.layout.addWidget(self.nav)
		self.layout.addWidget(self.canvas)

		self.setLayout(self.layout)
		self.canvas.ax.set_ylim((0, 5e-5))
		self.canvas.ax.set_xlim((0, .04))
		width = self.canvas.width()
		height = self.nav.height() + self.canvas.height() + 20
		self.setFixedSize(width, height)

        	

	def reset_opt(self):
		self.live_data = np.full(self.n_show, None)
	
	def live_plot(self):
		try:
		    this_shot = self.script(self.parent.data)
		    empty_data = np.where(self.live_data == None)
		    if len(empty_data[0]) == 0:
		        self.live_data[0:self.n_show - 1] = self.live_data[1:self.n_show]
		        self.live_data[-1] = this_shot
		    else:
		        self.live_data[empty_data[0][0]] = this_shot
		except AttributeError:
		    print('Not loaded')
		    
	'''def ones(self):
		return 1
	'''	
	def show_window(self):
		self.live_plot()
		self.canvas.ax.clear()
		self.canvas.ax.plot(self.live_data)
		self.canvas.ax.title(np.std(self.live_data))
		self.canvas.draw()
		
