import json
import numpy as np

from PyQt4 import QtGui, QtCore, Qt
from PyQt4.QtCore import pyqtSignal
from twisted.internet.defer import inlineCallbacks

from conductor.clients.smart_values_beta import SmartValuesClient


class MyClient(SmartValuesClient):
    servername = 'conductor'
    update_id = 461029
    updateTime = 100  # [ms]
    nameBoxWidth = 210
    valueBoxWidth = 90
    boxHeight = 20
    numRows = 18
    numCols = 4
    lat_top = ['sequencer.lat_top_deep', 'sequencer.lat_top_clock',
               'sequencer.lat_top_high', 'sequencer.lat_top_low']
    lat_bot = ['sequencer.lat_bot_deep', 'sequencer.lat_bot_clock',
               'sequencer.lat_bot_high', 'sequencer.lat_bot_low']
    lat_phase = ['sequencer.lat_phaseservo_offset', 'sequencer.lat_phaseservo_offset_deep',
                 'sequencer.lat_phaseservo_offset_clock', 'sequencer.lat_phaseservo_offset_low']
    lat_h = ['sequencer.lat_h_high', 'sequencer.lat_h_low',
             'sequencer.lat_h_ramp', 'sequencer.lat_h_clock']
    lat_params = lat_top + lat_bot + lat_phase + lat_h

    cav_params = ['cav_eom_amp_sg380', 'cav_eom_phase_sg380',
                  'sequencer.cav_sweep_low', 'sequencer.cav_sweep_high', 'sequencer.cav_fixed']

    clock_params = ['sequencer.clock_int_pi', 'sequencer.clock_phase',
                    'sequencer.clock_phase_align', 'sequencer.t_pi', 'sequencer.t_pi_2',
                    'sequencer.t_dark',
                    'sequencer.BxClock', 'sequencer.ByClock', 'sequencer.BzClock']
    defaults = [('lattice', lat_params), ('clock', clock_params),
                ('cavity', cav_params), ('other', ['sequencer.bLoad', 'sequencer.t_pump'])]


if __name__ == '__main__':
    app = QtGui.QApplication([])
    app.setWindowIcon(QtGui.QIcon('icon_image_paramVar.png'))
    from client_tools import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = MyClient(reactor)
    widget.show()
    reactor.run()
