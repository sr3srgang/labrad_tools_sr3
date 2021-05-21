import os
from data_analysis.pico import do_binned_fft
from pico.clients.pico_client import PicoViewer


class MyViewer(PicoViewer):
    #raw_data_path = '/home/srgang/K/data/pmt_data' #Single data file is overwritten every cycle to save HD space
    name = 'cavity_pico'
    data_dir = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    data_fxn = lambda _, x, ts: do_binned_fft(x, 1.6e-8) #number is sampling interval

if __name__ == '__main__':
    from PyQt4 import QtGui
    a = QtGui.QApplication([])
    import client_tools.qt4reactor as qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = MyViewer(reactor)
    widget.show()
    reactor.run()
