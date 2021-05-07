import os

from pmt.clients.pmt_client import PMTViewer


class MyViewer(PMTViewer):
    pmt_name = 'blue_pmt'
    data_dir = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')

if __name__ == '__main__':
    from PyQt4 import QtGui
    a = QtGui.QApplication([])
    import client_tools.qt4reactor as qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = MyViewer(reactor)
    widget.show()
    reactor.run()
