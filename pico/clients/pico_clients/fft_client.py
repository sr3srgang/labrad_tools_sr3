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
from data_analysis.pico import show_fft

from client_tools.connection import connection

class MplCanvas(FigureCanvas):
    def __init__(self):
        fig, ax = plt.subplots(1)
        self.fig = fig
        self.ax = ax

        self.fig.set_tight_layout(True)

        FigureCanvas.__init__(self, self.fig)
        self.setFixedSize(600, 300)

class FFTPlotter(QtGui.QDialog):
	
	
	def __init__(self, data, t):
		super(FFTPlotter, self).__init__()
		self.populate(t)
		self.show_plot(data)
		
    	def populate(self, t):
		self.setWindowTitle('FFT at time {} s'.format(t))
		self.canvas = MplCanvas()
		self.nav = NavigationToolbar(self.canvas, self)
		'''Changed nav toolbar'''
		
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

		
	def show_plot(self, data):
		
		self.canvas.ax.clear()
		self.canvas.ax.plot(data)
		self.canvas.draw()
