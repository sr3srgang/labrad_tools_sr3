import os

from sequencer.clients.default import SequencerClient

class TestClient(SequencerClient):
    conductor_servername = 'conductor'
    sequencer_servername = 'sequencer'
    sequence_directory = os.path.join(os.getenv('PROJECT_DATA_PATH'), 
                                      'sequences', '{}')
    master_channel = 'Trigger@D15'
    timing_channel = 'Trigger@D15'

if __name__ == '__main__':
    from PyQt4 import QtGui
    app = QtGui.QApplication([])
    import client_tools.qt4reactor as qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = TestClient(reactor)
    print widget.sequence_directory
    widget.show()
    reactor.run()
