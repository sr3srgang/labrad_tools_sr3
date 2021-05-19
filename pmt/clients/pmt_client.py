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

from client_tools.connection import connection

class MplCanvas(FigureCanvas):
    def __init__(self):
        fig, ax = plt.subplots(1)
        self.fig = fig
        self.ax = ax

        self.fig.set_tight_layout(True)

        FigureCanvas.__init__(self, self.fig)
        self.setFixedSize(600, 300)

class PMTViewer(QtGui.QDialog):
    pmt_name = None
    data_dir = None
    data_fxn = None

    def __init__(self, reactor, cxn=None):
        super(PMTViewer, self).__init__(None)
        self.reactor = reactor
        self.cxn = cxn
        print 'Directory:'
        print self.data_dir

        self.update_id = np.random.randint(0, 2**31 - 1)
        self.loading = False
        self.connect()
   
    @inlineCallbacks
    def connect(self):
        if self.cxn is None:
            self.cxn = connection()
            cname = 'pmt - {} - client'.format(self.pmt_name)
            yield self.cxn.connect(name=cname)

        self.populate()
        yield self.connect_signals()

    def populate(self):
        self.setWindowTitle(self.pmt_name)
        self.canvas = MplCanvas()
        self.nav = NavigationToolbar(self.canvas, self)
        
        self.layout = QtGui.QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.layout.addWidget(self.nav)
        self.layout.addWidget(self.canvas)

        self.setLayout(self.layout)
        self.canvas.ax.set_ylim((0, 1e-9))
        self.canvas.ax.set_xlim((0, .04))
        width = self.canvas.width()
        height = self.nav.height() + self.canvas.height() + 20
        self.setFixedSize(width, height)
        self.setWindowTitle('pmt_viewer')

    @inlineCallbacks
    def connect_signals(self):
        pmt_server = yield self.cxn.get_server('pmt')
        yield pmt_server.signal__update(self.update_id)
        yield pmt_server.addListener(listener=self.receive_update, source=None, 
                                     ID=self.update_id)

    def receive_update(self, c, signal_json):
        signal = json.loads(signal_json)
        for message_type, message in signal.items():
            print message_type, message
            device_message = message.get(self.pmt_name)
            if (message_type == 'record') and (device_message is not None):
                #Will only look at file specified by device message
                self.get_data(device_message)
                self.replot()

    def get_data(self, abs_data_path):
	with h5py.File(abs_data_path) as h5f:
            trig = h5f['trigger']
            self.data = np.array(trig)
    def replot(self):
        #abs_data_path = os.path.join(self.data_dir, rel_data_path) + '.hdf5'
        #with h5py.File(abs_data_path) as h5f:
         #   trig = h5f['trigger']
        trig = self.data
        #Apply function as specified in child class
        x, y = (self.data_fxn)(trig)
        #keep zoomed in view on repaint
        xlim = self.canvas.ax.get_xlim()
        ylim = self.canvas.ax.get_ylim()
        self.canvas.ax.clear()
        self.canvas.ax.plot(x, y, label='Time domain')
        self.canvas.ax.set_xlim(xlim)
        self.canvas.ax.set_ylim(ylim)
        self.canvas.ax.legend()
        self.canvas.draw()
    
    def closeEvent(self, x):
        self.reactor.stop()


        

