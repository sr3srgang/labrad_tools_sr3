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

    def __init__(self, reactor, cxn=None):
        super(PMTViewer, self).__init__(None)
        self.reactor = reactor
        self.cxn = cxn
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
                rdp = getattr(self, 'raw_data_path')
                if rdp:
                    self.replot(rdp)
                else:
                    self.replot(device_message)

    def replot(self, rel_data_path):
        abs_data_path = os.path.join(self.data_dir, rel_data_path) + '.hdf5'
        with h5py.File(abs_data_path) as h5f:
            gnd = h5f['gnd']
            exc = h5f['exc']
            bac = h5f['bac']
            self.canvas.ax.clear()
            self.canvas.ax.plot(gnd, label='gnd')
            self.canvas.ax.plot(exc, label='exc')
            self.canvas.ax.plot(bac, label='bac')
            self.canvas.ax.legend()
        self.canvas.draw()
    
    def closeEvent(self, x):
        self.reactor.stop()
        
class PMTViewerNumeric(PMTViewer):

    """ Class is modified to also display numeric readout of ground, excited,
    background and total counts.  These values update every time the plot is updated. 
    """

    def populate(self):
        self.setWindowTitle(self.pmt_name)
        self.canvas = MplCanvas()
        self.nav = NavigationToolbar(self.canvas, self)
        self.lcdGND = QtGui.QLCDNumber(self)
        self.lcdGND.display('0.001')
        self.lcdEXC = QtGui.QLCDNumber(self)
        self.lcdEXC.display('0.001')
        self.lcdBAC = QtGui.QLCDNumber(self)
        self.lcdBAC.display('0.000')
        self.lcdFRAC = QtGui.QLCDNumber(self)
        self.lcdFRAC.display('0.000')
        self.lcdTOTAL = QtGui.QLCDNumber(self)
        self.lcdTOTAL.display('0.000')
        self.labelGND = QtGui.QLabel('GROUND')
        self.labelGND.setAlignment(QtCore.Qt.AlignCenter)
        self.labelGND.setFont(QtGui.QFont("Arial", 48, QtGui.QFont.Bold))
        self.labelEXC = QtGui.QLabel('EXCITED')
        self.labelEXC.setAlignment(QtCore.Qt.AlignCenter)
        self.labelEXC.setFont(QtGui.QFont("Arial", 48, QtGui.QFont.Bold))
        self.labelBAC = QtGui.QLabel('BACKGROUND')
        self.labelBAC.setAlignment(QtCore.Qt.AlignCenter)
        self.labelBAC.setFont(QtGui.QFont("Arial", 48, QtGui.QFont.Bold))
        self.labelFRAC = QtGui.QLabel('EXC. FRACTION')
        self.labelFRAC.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFRAC.setFont(QtGui.QFont("Arial", 48, QtGui.QFont.Bold))
        self.labelTOTAL = QtGui.QLabel('TOTAL')
        self.labelTOTAL.setAlignment(QtCore.Qt.AlignCenter)
        self.labelTOTAL.setFont(QtGui.QFont("Arial", 48, QtGui.QFont.Bold))

         
        self.layout = QtGui.QGridLayout()
        self.layout.setSpacing(1)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.layout.addWidget(self.nav)
        self.layout.addWidget(self.canvas)
        
        self.hboxFRAC = QtGui.QHBoxLayout()
        self.hboxFRAC.addWidget(self.labelFRAC)
        self.hboxFRAC.addWidget(self.lcdFRAC)        
        self.hboxGND = QtGui.QHBoxLayout()
        self.hboxGND.addWidget(self.labelGND)
        self.hboxGND.addWidget(self.lcdGND)
        self.hboxEXC = QtGui.QHBoxLayout()
        self.hboxEXC.addWidget(self.labelEXC)
        self.hboxEXC.addWidget(self.lcdEXC)
        self.hboxBAC = QtGui.QHBoxLayout()
        self.hboxBAC.addWidget(self.labelBAC)
        self.hboxBAC.addWidget(self.lcdBAC)
        self.hboxTOTAL = QtGui.QHBoxLayout()
        self.hboxTOTAL.addWidget(self.labelTOTAL)
        self.hboxTOTAL.addWidget(self.lcdTOTAL)
        

        self.layout.addItem(self.hboxFRAC)
        self.layout.addItem(self.hboxGND)
        self.layout.addItem(self.hboxEXC)
        self.layout.addItem(self.hboxBAC)
        self.layout.addItem(self.hboxTOTAL)


        self.setLayout(self.layout)
       
        width = self.canvas.width() + 500
        height = self.nav.height() + self.canvas.height() + 8*self.lcdGND.height() + 200
        self.setFixedSize(width, height)
        self.setWindowTitle('PMT_trace_viewer')
        
                   
    def replot(self, rel_data_path):
        abs_data_path = os.path.join(self.data_dir, rel_data_path) + '.hdf5'
        with h5py.File(abs_data_path) as h5f:
            gnd = h5f['gnd']
            exc = h5f['exc']
            bac = h5f['bac']
            self.canvas.ax.clear()
            self.canvas.ax.plot(gnd, label='gnd')
            self.canvas.ax.plot(exc, label='exc')
            self.canvas.ax.plot(bac, label='bac')
            self.canvas.ax.legend()
            gnd = np.mean(h5f['gnd'][300:])
            exc = np.mean(h5f['exc'][300:])
            bac = np.mean(h5f['bac'][300:])
            tot = (gnd+exc-2*bac)
            if tot==0:
                frac = 0
            else:
                frac = (exc-bac)/tot
            self.lcdGND.display(str(np.round(gnd,3)))
            self.lcdEXC.display(str(np.round(exc,3)))
            self.lcdBAC.display(str(np.round(bac,3)))
            self.lcdFRAC.display(str(np.round(frac,3)))
            self.lcdTOTAL.display(str(np.round(tot,3)))
        self.canvas.draw()
                            

    
