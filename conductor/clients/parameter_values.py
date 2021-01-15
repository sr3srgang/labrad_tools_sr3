import json
import numpy as np

from PyQt4 import QtGui, QtCore, Qt
from PyQt4.QtCore import pyqtSignal
from twisted.internet.defer import inlineCallbacks

from client_tools.connection import connection
from client_tools.widgets import NeatSpinBox

class ParameterRow(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self)
        self.boxWidth = parent.boxWidth
        self.boxHeight = parent.boxHeight
        self.populateGUI()

    def loadControlConfiguration(self, configuration):
        for key, value in configuration.__dict__.items():
            setattr(self, key, value)
    
    def populateGUI(self):
        self.nameBox = QtGui.QLineEdit()
        self.nameBox.setFixedSize(self.boxWidth, self.boxHeight)
        self.valueBox = NeatSpinBox()
        self.valueBox.setFixedSize(self.boxWidth, self.boxHeight)

        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.nameBox)
        self.layout.addWidget(self.valueBox)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

class ParameterValuesClient(QtGui.QGroupBox):
    hasNewValue = False
    free = True

    def __init__(self, reactor, cxn=None):
        QtGui.QDialog.__init__(self)
        self.reactor = reactor
        self.cxn = cxn
        self.connect()

    @inlineCallbacks
    def connect(self):
        if self.cxn is None:
            self.cxn = connection()
            cname = '{} - client'.format(self.servername)
            yield self.cxn.connect(name=cname)
        self.context = yield self.cxn.context()
        try:
            self.populateGUI()
            yield self.connectSignals()
        except Exception, e:
            print e
            self.setDisabled(True)

    def populateGUI(self):
        self.parameterRows = [ParameterRow(self) 
                for i in range(self.numRows)]

        self.layout = QtGui.QVBoxLayout()
        for pr in self.parameterRows:
            self.layout.addWidget(pr)
        self.layout.setSpacing(1)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.setFixedSize(2*(self.boxWidth+2), self.numRows*(self.boxHeight+2))
        self.setLayout(self.layout)

    @inlineCallbacks
    def connectSignals(self):
        server = yield self.cxn.get_server(self.servername)
        yield server.signal__update(self.update_id)
        yield server.addListener(listener=self.receive_update, source=None,
                                 ID=self.update_id)
        yield self.cxn.add_on_connect(self.servername, self.reinit)
        yield self.cxn.add_on_disconnect(self.servername, self.disable)

        for pr in self.parameterRows:
            pr.nameBox.returnPressed.connect(self.get_parameter_value(pr))
            pr.valueBox.returnPressed.connect(self.set_parameter_value(pr))
    
    def receive_update(self, c, signal_json):
        signal = json.loads(signal_json)
        for message_type, message in signal.items():
            if message_type in ['get_parameter_values', 'set_parameter_values']:
                for pr in self.parameterRows:
                    parameterName = str(pr.nameBox.text())
                    if parameterName in message:
                        pr.valueBox.display(message[parameterName])

    def set_parameter_value(self, parameterRow):
        @inlineCallbacks
        def spv():
            name = str(parameterRow.nameBox.text())
            value = float(parameterRow.valueBox.value())
            server = yield self.cxn.get_server(self.servername)
            request = {name: value}
            yield server.set_parameter_values(json.dumps(request))
            parameterRow.valueBox.display(value)
        return spv
    
    def get_parameter_value(self, parameterRow):
        @inlineCallbacks
        def gpv():
            name = str(parameterRow.nameBox.text())
            server = yield self.cxn.get_server(self.servername)
            request = {name: None}
            response_json = yield server.get_parameter_values(json.dumps(request))
            response = json.loads(response_json)
            value = response[name]
            parameterRow.valueBox.display(value)
        return gpv

    @inlineCallbacks
    def set_parameter_values(self):
        server = yield self.cxn.get_server(self.servername)
        request = {str(pr.nameBox.text()): float(pr.valueBox.value()) for pr in self.parameterRows 
                   if str(pr.nameBox.text())}
        response_json = yield server.set_parameter_values(json.dumps(request))
        response = json.loads(response_json)
        for pr in self.parameterRows:
            parameterName = str(pr.nameBox.text())
            if parameterName in response:
                pr.valueBox.display(response[parameterName])
    
    @inlineCallbacks
    def get_parameter_values(self):
        server = yield self.cxn.get_server(self.servername)
        request = {str(pr.nameBox.text()): None for pr in self.parameterRows 
                   if str(pr.nameBox.text())}
        response_json = yield server.get_parameter_values(json.dumps(request))
        response = json.loads(response_json)
        for pr in self.parameterRows:
            parameterName = str(pr.nameBox.text())
            if parameterName in response:
                pr.valueBox.display(response[parameterName])


    @inlineCallbacks	
    def reinit(self): 
        self.setDisabled(False)
        server = yield self.cxn.get_server(self.servername)
        yield server.signal__update(self.update_id, context=self.context)
        yield server.addListener(listener=self.receive_update, source=None,
                                 ID=self.update_id, context=self.context)

    def disable(self):
        self.setDisabled(True)

    def closeEvent(self, x):
        self.reactor.stop()
