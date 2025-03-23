from client_tools.connection3 import connection
from data_analysis.pico import show_fft
from data_analysis.cavity_clock.read_data_oldBackup import get_cavity_data
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QDialog, QGridLayout, QMenu, QComboBox, QPushButton
from PyQt5.QtCore import QTimer, QDateTime
import matplotlib.pyplot as plt

from PyQt5 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks, returnValue
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')


class MplCanvas(FigureCanvas):
    def __init__(self):
        fig, ax = plt.subplots(1)
        self.fig = fig
        fig.patch.set_facecolor('black')
        self.ax = ax
        ax.set_facecolor('xkcd:grey')
        plt.rcParams.update({'font.size': 16, 'text.color': 'white'})
        ax.yaxis.label.set_color('white')
        ax.xaxis.label.set_color('white')
        ax.tick_params(color='white', labelcolor='white')
        self.fig.set_tight_layout(True)

        FigureCanvas.__init__(self, self.fig)
        self.setFixedSize(600, 300)



class FFTPlotter(QDialog):
    def __init__(self, update, t):
        super(FFTPlotter, self).__init__()
        self.populate()
        self.show_plot(update, t)

    def populate(self):
        self.setWindowTitle("FFT")
        self.canvas = MplCanvas()
        self.nav = NavigationToolbar(self.canvas, self)
        '''Changed nav toolbar'''

        self.layout = QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.layout.addWidget(self.nav)
        self.layout.addWidget(self.canvas)

        self.setLayout(self.layout)
        width = self.canvas.width()
        height = self.nav.height() + self.canvas.height()
        self.setFixedSize(width, height)

    def show_plot(self, update, t, trace = 'gnd'):
        self.canvas.ax.set_facecolor('xkcd:pinkish grey')
        for message_type, message in update.items():
            value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            data, ts = get_cavity_data(value, trace)
            Pxx, freqs, t0 = show_fft(data, ts, t)
            self.setWindowTitle('FFT at time {} s'.format(t0))
            self.canvas.ax.clear()
            self.canvas.ax.plot(freqs*1e-6, Pxx, 'k')
            self.canvas.ax.set_xlim((0, 10))
            self.canvas.ax.set_xlabel("Freq (MHz)")
            self.canvas.draw()
        
        
        
