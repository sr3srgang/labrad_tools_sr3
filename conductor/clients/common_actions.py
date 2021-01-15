import json
import numpy as np
import sys

from PyQt4 import QtGui, QtCore, Qt
from PyQt4.QtCore import pyqtSignal
from twisted.internet.defer import inlineCallbacks

from client_tools.connection import connection
from client_tools.widgets import SuperSpinBox

ACTION_WIDTH = 120
ACTION_HEIGHT = 50

class ButtonActionWidget(QtGui.QPushButton):
    name = None
    servername = None

    def __init__(self, reactor, cxn=None):
        QtGui.QDialog.__init__(self)
        self.reactor = reactor
        self.cxn = cxn 
        self.initialize()

    @inlineCallbacks
    def initialize(self):
        if self.cxn is None:
            self.cxn = connection()
            cname = '{} - {} - client'.format(self.servername, self.name)
            yield self.cxn.connect(name=cname)
        self.populateGUI()
        yield self.connectSignals()
    
    def populateGUI(self):
#        self.action_button = QtGui.QPushButton()
#        self.action_button.setText(self.name)
#        self.layout = QtGui.QGridLayout()
#        self.layout.addWidget(self.action_button)
        self.setText(self.name)
        
        self.setWindowTitle(self.name)
#        self.setLayout(self.layout)
        self.setFixedSize(ACTION_WIDTH , ACTION_HEIGHT)

    @inlineCallbacks
    def connectSignals(self):
        yield self.cxn.add_on_connect(self.servername, self.reinitialize)
        yield self.cxn.add_on_disconnect(self.servername, self.disable)
#        self.action_button.released.connect(self.onButtonPressed)
        self.released.connect(self.onButtonPressed)
    
    @inlineCallbacks
    def onButtonPressed(self):
        pass
    
    def reinitialize(self):
        self.setDisabled(False)

    def disable(self):
        self.setDisabled(True)

    def closeEvent(self, x):
        self.reactor.stop()

class RunBlueMOT(ButtonActionWidget):
    name = 'Run Blue MOT'
    servername = 'conductor'

    @inlineCallbacks
    def onButtonPressed(self):
        server = yield self.cxn.get_server(self.servername)
        request = {'sequencer.sequence': ['blue_mot_ss']}
        yield server.set_parameter_values(json.dumps(request))

class StopExperiment(ButtonActionWidget):
    name = 'Stop Experiment'
    servername = 'conductor'

    @inlineCallbacks
    def onButtonPressed(self):
        server = yield self.cxn.get_server(self.servername)
        yield server.stop_experiment()
        
#class CommonActionsClient(QtGui.QGroupBox):
#    servername = 'conductor'
#
#    def __init__(self, reactor, cxn=None):
#        QtGui.QDialog.__init__(self)
#        self.reactor = reactor
#        self.cxn = cxn 
#        self.connect()
#
#    @inlineCallbacks
#    def connect(self):
#        if self.cxn is None:
#            self.cxn = connection()
#            cname = '{} - {} - client'.format(self.servername, self.name)
#            yield self.cxn.connect(name=cname)
#        yield self.select_device()
#        self.populateGUI()
#        yield self.connectSignals()
#        yield self.requestValues()
#
#    def populateGUI(self):
#        self.state_button = QtGui.QPushButton()
#        self.state_button.setCheckable(1)
#        
#        self.piezo_voltage_box = SuperSpinBox(self.piezo_voltage_range, 
#                                          self.piezo_voltage_display_units, 
#                                          self.piezo_voltage_digits)
#        self.piezo_voltage_box.setFixedWidth(self.spinbox_width)
#        self.piezo_voltage_box.display(0)
#        
#        self.diode_current_box = SuperSpinBox(self.diode_current_range, 
#                                          self.diode_current_display_units, 
#                                          self.diode_current_digits)
#        self.diode_current_box.setFixedWidth(self.spinbox_width)
#        self.diode_current_box.display(0)
#
#        self.layout = QtGui.QGridLayout()
#        
#        row = 0
#        self.layout.addWidget(QtGui.QLabel('<b>'+self.name+'</b>'), 
#                              0, 0, 1, 1, QtCore.Qt.AlignHCenter)
#        if 'state' in self.update_parameters:
#            self.layout.addWidget(self.state_button, 0, 1)
#        else:
#            self.layout.addWidget(QtGui.QLabel('always on'), 
#                                  0, 0, 1, 1, QtCore.Qt.AlignHCenter)
#        if 'piezo_voltage' in self.update_parameters:
#            row += 1
#            self.piezo_voltage_label = ParameterLabel('Piezo Voltage: ')
#            self.layout.addWidget(self.piezo_voltage_label, 
#                                  row, 0, 1, 1, QtCore.Qt.AlignRight)
#            self.layout.addWidget(self.piezo_voltage_box, row, 1)
#        if 'diode_current' in self.update_parameters:
#            row += 1
#            self.diode_current_label = ParameterLabel('Diode Current: ')
#            self.layout.addWidget(self.diode_current_label, 
#                                  row, 0, 1, 1, QtCore.Qt.AlignRight)
#            self.layout.addWidget(self.diode_current_box, row, 1)
#
#        self.setWindowTitle(self.name)
#        self.setLayout(self.layout)
#        self.setFixedSize(ACTION_HEIGHT + self.spinbox_width, 100)
#
#    @inlineCallbacks
#    def connectSignals(self):
#        self.hasNewState = False
#        self.hasNewPiezoVoltage = False
#        self.hasNewDiodeCurrent = False
#        server = yield self.cxn.get_server(self.servername)
#        yield server.signal__update(self.update_id)
#        yield server.addListener(listener=self.receive_update, source=None, 
#                                 ID=self.update_id)
#        yield self.cxn.add_on_connect(self.servername, self.reinitialize)
#        yield self.cxn.add_on_disconnect(self.servername, self.disable)
#
#        self.state_button.released.connect(self.onNewState)
#        self.piezo_voltage_box.returnPressed.connect(self.onNewPiezoVoltage)
#        self.diode_current_box.returnPressed.connect(self.onNewDiodeCurrent)
#
#        if 'piezo_voltage' in self.update_parameters:
#            self.piezo_voltage_label.clicked.connect(self.requestValues)
#        if 'diode_current' in self.update_parameters:
#            self.diode_current_label.clicked.connect(self.requestValues)
#        
#        self.timer = QtCore.QTimer(self)
#        self.timer.timeout.connect(self.writeValues)
#        self.timer.start(self.update_time)
#
#    @inlineCallbacks
#    def requestValues(self, c=None):
#        server = yield self.cxn.get_server(self.servername)
#        request = {self.name: None}
#        for parameter in self.update_parameters:
#            yield getattr(server, parameter + 's')(json.dumps(request))
# 
#    def receive_update(self, c, signal_json):
#        signal = json.loads(signal_json)
#        for message_type, message in signal.items():
#            device_message = message.get(self.name)
#            if (message_type == 'states') and (device_message is not None):
#                self.free = False
#                if device_message:
#                    self.state_button.setChecked(1)
#                    self.state_button.setText('On')
#                else:
#                    self.state_button.setChecked(0)
#                    self.state_button.setText('Off')
#                self.free = True
#            if (message_type == 'piezo_voltages') and (device_message is not None):
#                self.free = False
#                self.piezo_voltage_box.display(device_message)
#                self.free = True
#            if (message_type == 'diode_currents') and (device_message is not None):
#                self.free = False
#                self.diode_current_box.display(device_message)
#                self.free = True
#
#    @inlineCallbacks
#    def onNewState(self):
#        if self.free:
#            server = yield self.cxn.get_server(self.servername)
#            is_on = yield server.state()
#            if is_on:
#                yield server.shutdown()
#            else:
#                yield server.warmup()
#
#    def onNewPiezoVoltage(self):
#        if self.free:
#            self.hasNewPiezoVoltage = True
#   
#    def onNewDiodeCurrent(self):
#        if self.free:
#            self.hasNewDiodeCurrent = True
#
#    @inlineCallbacks
#    def writeValues(self):
#        if self.hasNewPiezoVoltage:
#            server = yield self.cxn.get_server(self.servername)
#            request = {self.name: self.piezo_voltage_box.value()}
#            yield server.piezo_voltages(json.dumps(request))
#            self.hasNewPiezoVoltage = False
#        elif self.hasNewDiodeCurrent:
#            server = yield self.cxn.get_server(self.servername)
#            request = {self.name: self.diode_current_box.value()}
#            yield server.diode_currents(json.dumps(request))
#            self.hasNewDiodeCurrent = False
#           
#    def reinitialize(self):
#        self.setDisabled(False)
#
#    def disable(self):
#        self.setDisabled(True)
#
#    def closeEvent(self, x):
#        self.reactor.stop()

class MultipleActionsContainer(QtGui.QWidget):
    name = None
    def __init__(self, client_list, reactor, cxn=None):
        QtGui.QDialog.__init__(self)
        self.client_list = client_list
        self.reactor = reactor
        self.initialize()
 
    def initialize(self):
        self.populateGUI()

    def populateGUI(self):
        self.layout = QtGui.QVBoxLayout()
        for client in self.client_list:
            self.layout.addWidget(client)
        self.setFixedSize(ACTION_WIDTH + 20 , (ACTION_HEIGHT + 12) * len(self.client_list) )
        self.setLayout(self.layout)
        self.setWindowTitle('conductor - common actions')

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == '__main__':
    from PyQt4 import QtGui
    app = QtGui.QApplication([])
    from client_tools import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widgets = [
        RunBlueMOT(reactor),
        StopExperiment(reactor),
        ]
    widget = MultipleActionsContainer(widgets, reactor)
    widget.show()
    reactor.run()
