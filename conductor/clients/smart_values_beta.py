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
        self.nameBoxWidth = parent.nameBoxWidth
        self.valueBoxWidth = parent.valueBoxWidth
        self.boxHeight = parent.boxHeight
        self.populateGUI()

    def loadControlConfiguration(self, configuration):
        for key, value in configuration.__dict__.items():
            setattr(self, key, value)

    def populateGUI(self):
        self.nameBox = QtGui.QLineEdit()
        self.nameBox.setFixedSize(self.nameBoxWidth, self.boxHeight)
        self.valueBox = NeatSpinBox()
        self.valueBox.setFixedSize(self.valueBoxWidth, self.boxHeight)

        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.nameBox)
        self.layout.addWidget(self.valueBox)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)


# create a column of numRows parameter rows
class ParameterColumn(QtGui.QGroupBox):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self)
        self.numRows = parent.numRows
        self.nameBoxWidth = parent.nameBoxWidth
        self.valueBoxWidth = parent.valueBoxWidth
        self.boxHeight = parent.boxHeight
        self.populateGUI()

    def populateGUI(self):
        self.parameterRows = [ParameterRow(self)
                              for i in range(self.numRows)]

        self.layout = QtGui.QVBoxLayout()
        for pr in self.parameterRows:
            self.layout.addWidget(pr)
        self.layout.setSpacing(1)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.setFixedSize(self.nameBoxWidth + self.valueBoxWidth +
                          4, self.numRows*(self.boxHeight+2))
        self.setLayout(self.layout)

# create a grid of numCols ParameterColumns


class ParameterGrid(QtGui.QGroupBox):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self)
        self.numRows = parent.numRows
        self.numCols = parent.numCols
        self.nameBoxWidth = parent.nameBoxWidth
        self.valueBoxWidth = parent.valueBoxWidth
        self.boxHeight = parent.boxHeight
        self.populateGUI()

    def populateGUI(self):
        self.parameterCols = [ParameterColumn(
            self) for i in range(self.numCols)]

        self.layout = QtGui.QHBoxLayout()

        for pc in self.parameterCols:
            self.layout.addWidget(pc)

        self.layout.setSpacing(1)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.setFixedSize((1 + self.numCols)*(self.nameBoxWidth + self.valueBoxWidth +
                          4),
                          (2 + self.numRows)*(self.boxHeight+2))
        # self.updateAll_button = QtGui.QTabWidget()
        # self.setWindowTitle('test')

        self.setLayout(self.layout)


class SmartValuesClient(QtGui.QGroupBox):
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
        self.paramGrid = ParameterGrid(self)
        self.parameterCols = self.paramGrid.parameterCols

        self.refreshButton = QtGui.QPushButton('refresh all vals', self)
        self.saveButton = QtGui.QPushButton('save to .vals', self)
        # self.refreshButton.clicked.connect(HERE)

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.paramGrid, 1, 0, 4, 8)
        self.layout.addWidget(self.refreshButton, 0, 4, 1, 1)
        self.layout.addWidget(self.saveButton, 0, 6, 1, 1)

        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setWindowTitle('beta conductor client')
        # self.setWindowTitle('test')

        self.setLayout(self.layout)

        #
        # self.updateAll_button.setTabPosition(QtGui.QTabWidget.North)
        # self.layout.addWidget(self.updateAll_button)

    @inlineCallbacks
    def connectSignals(self):
        server = yield self.cxn.get_server(self.servername)
        yield server.signal__update(self.update_id)
        yield server.addListener(listener=self.receive_update, source=None,
                                 ID=self.update_id)
        yield self.cxn.add_on_connect(self.servername, self.reinit)
        yield self.cxn.add_on_disconnect(self.servername, self.disable)

        for i in range(self.numCols):
            pc = self.parameterCols[i]
            title, params = self.defaults[i]
            pc.setTitle(title)

            for pr in pc.parameterRows:
                pr.nameBox.returnPressed.connect(self.get_parameter_value(pr))
                pr.valueBox.returnPressed.connect(self.set_parameter_value(pr))

            for j in range(len(params)):
                pr = pc.parameterRows[j]
                nb = pr.nameBox
                nb.setText(params[j])
                self.get_parameter_value(pr)()
                nb.setReadOnly(True)
                nb.setStyleSheet("background-color: rgb(229, 193, 197)")

    def receive_update(self, c, signal_json):
        signal = json.loads(signal_json)
        for message_type, message in signal.items():
            if message_type in ['get_parameter_values', 'set_parameter_values']:
                for pc in self.parameterCols:
                    for pr in pc.parameterRows:
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
