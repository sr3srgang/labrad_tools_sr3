import sys
from PyQt4 import QtGui, QtCore, Qt
from PyQt4.QtCore import pyqtSignal
from twisted.internet.defer import inlineCallbacks
import traceback
import numpy as np
import json

from client_tools.connection import connection
from client_tools.widgets import SuperSpinBox

class AnalogVoltageManualClient(QtGui.QGroupBox):
    hasNewVoltage = False
    mouseHover = pyqtSignal(bool)
    layout = None
    update_time = 100 # [ms]
    voltage_range = (-10., 10.)
    voltage_units = [(0, 'V')]
    voltage_digits = 3
    spinbox_width = 80

    mode = None
    manual_output = None

    def __init__(self, reactor, cxn=None, parent=None):
        try:
            QtGui.QDialog.__init__(self)
            self.reactor = reactor
            self.cxn = None
            self.parent = parent
            self.sequencer_update_id = np.random.randint(0, 2**31 - 1)
            
            self.connect()
        except Exception, e:
            print e
            traceback.print_exc()

    @inlineCallbacks
    def connect(self):
        if self.cxn is None:
            self.cxn = connection()
            yield self.cxn.connect()
        print 1
        self.populateGUI()
        print 2
        yield self.connectSignals()
        print 3
        yield self.getChannelInfo()
        print 4
        self.updateDisplay()

    @inlineCallbacks
    def get_server_configuration(self):
        yield None

    def populateGUI(self):
        self.mode_button = QtGui.QPushButton()
        self.mode_button.setCheckable(1)
        self.mode_button.setFixedWidth(self.spinbox_width)
        
        self.voltage_box = SuperSpinBox(self.voltage_range, self.voltage_units,
                                        self.voltage_digits)
        self.voltage_box.setFixedWidth(self.spinbox_width)
        self.voltage_box.display(0)

        if self.layout is None:
            self.layout = QtGui.QGridLayout()

        self.layout.addWidget(QtGui.QLabel('<b>'+self.name+'</b>'), 1, 0, 1, 1,
                              QtCore.Qt.AlignHCenter)
        self.layout.addWidget(self.mode_button, 1, 1)
        self.layout.addWidget(QtGui.QLabel('Voltage: '), 2, 0, 1, 1,
                              QtCore.Qt.AlignRight)
        self.layout.addWidget(self.voltage_box, 2, 1)
        self.setLayout(self.layout)
        self.setFixedSize(100 + self.spinbox_width, 90)

    @inlineCallbacks
    def connectSignals(self):
        server = yield self.cxn.get_server(self.sequencer_servername)
        yield server.signal__update(self.sequencer_update_id)
        yield server.addListener(listener=self.receive_sequencer_update,
                                 source=None, ID=self.sequencer_update_id)
        yield self.cxn.add_on_connect(self.sequencer_servername, self.reinit)
        yield self.cxn.add_on_disconnect(self.sequencer_servername, self.disable)

        self.mode_button.released.connect(self.onNewMode)
        self.voltage_box.returnPressed.connect(self.onNewVoltage)
        self.setMouseTracking(True)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.writeValues)
        self.timer.start(self.update_time)

    @inlineCallbacks
    def getChannelInfo(self, x=None):
        server = yield self.cxn.get_server(self.sequencer_servername)
        request = {self.board_name: {self.name: None}}
        response_json = yield server.get_channel_infos(json.dumps(request))
        response = json.loads(response_json)
        info = response[self.board_name][self.name]
        for k, v in info.items():
            setattr(self, k, v)

    def updateDisplay(self):
        self.free = False
        if self.mode == 'manual':
            self.mode_button.setChecked(1)
            self.mode_button.setText('Manual')
        if self.mode == 'auto':
            self.mode_button.setChecked(0)
            self.mode_button.setText('Auto')
        self.voltage_box.display(float(self.manual_output))
        self.free = True

    def receive_sequencer_update(self, c, signal_json):
        signal = json.loads(signal_json)
        for message_type, message in signal.items():
            if message_type == 'channel_manual_outputs':
                manual_output = message.get(self.board_name, {}).get(self.name)
                if manual_output is not None:
                    self.manual_output = float(manual_output)
            if message_type == 'channel_modes':
                mode = message.get(self.board_name, {}).get(self.name)
                if mode is not None:
                    self.mode = mode
        self.updateDisplay()

    def enterEvent(self, c):
        self.mouseHover.emit(True)

    def leaveEvent(self, c):
        self.mouseHover.emit(True)

    @inlineCallbacks
    def onNewMode(self):
        if self.free:
            if self.mode == 'manual':
                mode = 'auto'
            else:
                mode = 'manual'
            server = yield self.cxn.get_server(self.sequencer_servername)
            request = {self.board_name: {self.name: mode}}
            response_json = yield server.channel_modes(json.dumps(request))
            response = json.loads(response_json)
            self.mode = response[self.board_name][self.name]
        self.updateDisplay()


    @inlineCallbacks
    def writeValues(self):
        if self.hasNewVoltage:
            server = yield self.cxn.get_server(self.sequencer_servername)
            manual_output = self.voltage_box.value()
            request = {self.board_name: {self.name: manual_output}}
            response_json = yield server.channel_manual_outputs(json.dumps(request))
            response = json.loads(response_json)
            self.manual_output = response[self.board_name][self.name]
            self.hasNewVoltage = False
        self.updateDisplay()

    def onNewVoltage(self):
        if self.free:
            self.hasNewVoltage = True

    @inlineCallbacks	
    def reinit(self): 
        self.setDisabled(False)
        server = yield self.cxn.get_server(self.servername)
        yield server.signal__update(self.update_id, context=self.context)
        yield server.addListener(listener=self.receive_update, source=None,
                                 ID=self.update_id, context=self.context)
        yield server.send_update()


    def disable(self):
        self.setDisabled(True)
    
    @inlineCallbacks
    def closeEvent(self, event):
        sequencer = yield self.cxn.get_server(self.sequencer_servername)
        yield sequencer.signal__update(self.sequencer_update_id)
        yield sequencer.removeListener(listener=self.receive_sequencer_update, source=None,
                                    ID=self.sequencer_update_id)
        if self.parent is None:
            self.reactor.stop()

        event.accept()

#if __name__ == '__main__':
#    import sys
#    a = QtGui.QApplication([])
#    import qt4reactor
#    qt4reactor.install()
#    from twisted.internet import reactor
#    conf = ClientConfig()
#    widget = AnalogVoltageManualClient(conf, reactor)
#    widget.show()
#    reactor.run()
