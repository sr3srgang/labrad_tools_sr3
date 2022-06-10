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
from pico.clients.pico_clients.plotter_client import PicoPlotter
from pico.clients.pico_clients.fft_client import FFTPlotter
from client_tools.connection import connection

class MplCanvas(FigureCanvas):
    def __init__(self):
        fig, ax = plt.subplots(1)
        self.fig = fig
        self.ax = ax

        self.fig.set_tight_layout(True)

        FigureCanvas.__init__(self, self.fig)
        self.setFixedSize(1200, 600)

class PicoViewer(QtGui.QDialog):
    name = None
    data_dir = None
    data_fxn = None

    def __init__(self, reactor, cxn=None, ylim = 2e-9):
        super(PicoViewer, self).__init__(None)
        self.reactor = reactor
        self.cxn = cxn
        print 'Directory:'
        print self.data_dir

        self.update_id = np.random.randint(0, 2**31 - 1)
        self.loading = False
        self.connect()
        
        self.Plotter = PicoPlotter(self)
   
    @inlineCallbacks
    def connect(self):
        if self.cxn is None:
            self.cxn = connection()
            cname = 'pico - {} - client'.format(self.name)
            yield self.cxn.connect(name=cname)

        self.populate()
        yield self.connect_signals()

    def show_fft(self):
    	self.mouse_listener = self.canvas.mpl_connect('button_press_event', self.process_click)
    
    def process_click(self, event):
    	t_click = event.xdata
    	self.canvas.mpl_disconnect(self.mouse_listener)
    	self.FFTPlot = FFTPlotter(self.data, self.ts, t_click)
    	self.FFTPlot.show()

    def launch_plotter(self):
    	self.Plotter.show()
    	
    def populate(self):
        self.setWindowTitle(self.name)
        self.canvas = MplCanvas()
        self.nav = NavigationToolbar(self.canvas, self)
        self.nav.addAction('Select analysis method')
        self.nav.addAction('Launch live plotter', self.launch_plotter)
        self.nav.addAction('Show fft on click', self.show_fft)
        
  
        self.layout = QtGui.QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.layout.addWidget(self.nav)
        self.layout.addWidget(self.canvas)

        self.setLayout(self.layout)
        self.canvas.ax.set_ylim(self.ylim)
        self.canvas.ax.set_xlim((-.005, .045))
        width = self.canvas.width()
        height = self.nav.height() + self.canvas.height() + 20
        self.setFixedSize(width, height)
        self.setWindowTitle('pico_viewer')

    @inlineCallbacks
    def connect_signals(self):
        pico_server = yield self.cxn.get_server('cavity_probe_pico')
        yield pico_server.signal__update(self.update_id)
        yield pico_server.addListener(listener=self.receive_update, source=None, ID=self.update_id)

    def receive_update(self, c, signal_json):
        signal = json.loads(signal_json)
        for message_type, message in signal.items():
            print message_type, message
            device_message = message.get(self.name)
            if (message_type == 'record') and (device_message is not None):
                #Will only look at file specified by device message
                self.get_data(device_message)
                self.replot()
                self.Plotter.show_window()
                

    def get_data(self, abs_data_path):
	with h5py.File(abs_data_path) as h5f:
            self.data = np.array(h5f['gnd'])
            #self.test = np.array(h5f['test_new_trig'])
            #print(self.test)
            self.ts = np.array(h5f['time'])
            
    def replot(self):
        #Apply function as specified in child class
        print('called')
        x, y = (self.data_fxn)(self.data, self.ts)#, self.ts)
        #keep zoomed in view on repaint
        xlim = self.canvas.ax.get_xlim()
        ylim = self.canvas.ax.get_ylim()
        self.canvas.ax.clear()
        self.canvas.ax.plot(x, y, label='Time domain')
        self.canvas.ax.set_xlim(xlim)
        self.canvas.ax.set_ylim(ylim)
        self.canvas.ax.legend()
        self.canvas.draw()
        print('redrawn')
    
    def closeEvent(self, x):
        self.reactor.stop()


        

