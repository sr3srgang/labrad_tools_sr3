import json
import numpy as np
import time

from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks

from client_tools.widgets import ClickableLabel

class CurrentControllerClient(QtGui.QGroupBox):
    name = None
    DeviceProxy = None
    currentStepsize = 0.0001
    lockedColor = '#80ff80'
    unlockedColor = '#ff8080'
    updateID = np.random.randint(0, 2**31 - 1)
    
    def __init__(self, reactor):
        QtGui.QDialog.__init__(self)
        self.reactor = reactor
        reactor.callInThread(self.initialize)
        self.connectLabrad()
    
    @inlineCallbacks
    def connectLabrad(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(name=self.name)
        yield self.cxn.update.signal__signal(self.updateID)
        yield self.cxn.update.addListener(listener=self.receiveUpdate, source=None, 
                                          ID=self.updateID)
        yield self.cxn.update.register(self.name)

    def receiveUpdate(self, c, updateJson):
        update = json.loads(updateJson)
        state = update.get('state')
        if state is not None:
            self.displayState(state)
        current = update.get('current')
        if current is not None:
            self.displayCurrent(current)
        power = update.get('power')
        if power is not None:
            self.displayPower(power)

    def initialize(self):
        import labrad
        cxn = labrad.connect(name=self.name)
        self.device = self.DeviceProxy(cxn)
        self.reactor.callFromThread(self.populateGUI)
        self.reactor.callFromThread(self.connectSignals)
    
    def populateGUI(self):
        self.nameLabel = ClickableLabel('<b>'+self.name+'</b>')
        self.stateButton = QtGui.QPushButton()
        self.stateButton.setCheckable(1)
        
        self.currentLabel = ClickableLabel('Current [A]: ')
        self.currentBox = QtGui.QDoubleSpinBox()
        self.currentBox.setKeyboardTracking(False)
        self.currentBox.setRange(*self.device._current_range)
        self.currentBox.setSingleStep(self.currentStepsize)
        self.currentBox.setDecimals(
                abs(int(np.floor(np.log10(self.currentStepsize)))))
        self.currentBox.setAccelerated(True)

        self.powerLabel = ClickableLabel('Power [mW]: ')
        self.powerBox = QtGui.QDoubleSpinBox()
        self.powerBox.setRange(0, 1e3)
        self.powerBox.setReadOnly(True)
        self.powerBox.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        self.powerBox.setDecimals(4)

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.nameLabel, 1, 0, 1, 1, 
                              QtCore.Qt.AlignHCenter)
        self.layout.addWidget(self.stateButton, 1, 1)
        self.layout.addWidget(self.currentLabel, 2, 0, 1, 1, 
                              QtCore.Qt.AlignRight)
        self.layout.addWidget(self.currentBox, 2, 1)
        self.layout.addWidget(self.powerLabel, 3, 0, 1, 1, 
                              QtCore.Qt.AlignRight)
        self.layout.addWidget(self.powerBox, 3, 1)

        self.setWindowTitle(self.name)
        self.setLayout(self.layout)
        self.setFixedSize(200, 120)
    
        self.reactor.callInThread(self.getAll)
    
    def getAll(self):
        self.getState()
        self.getCurrent()
        self.getPower()
    
    def getState(self):
        state = self.device.state
        self.reactor.callFromThread(self.displayState, state)

    def displayState(self, state):
        if state:
            self.stateButton.setChecked(1)
            self.stateButton.setText('On')
        else:
            self.stateButton.setChecked(0)
            self.stateButton.setText('Off')
    
    def getCurrent(self):
        current = self.device.current
        self.reactor.callFromThread(self.displayCurrent, current)

    def displayCurrent(self, current):
        self.currentBox.setValue(current)
    
    def getPower(self):
        power = self.device.power
        self.reactor.callFromThread(self.displayPower, power)

    def displayPower(self, power):
        self.powerBox.setValue(power * 1e3)
        if hasattr(self.device, '_locked_threshold'):
            if power > self.device._locked_threshold:
                self.powerBox.setStyleSheet('QWidget {background-color: %s}' % self.lockedColor)
            else:
                self.powerBox.setStyleSheet('QWidget {background-color: %s}' % self.unlockedColor)
    
    def connectSignals(self):
        self.stateButton.released.connect(self.onNewState)
        self.currentBox.valueChanged.connect(self.onNewCurrent)
        
        self.nameLabel.clicked.connect(self.onNameLabelClick)
        self.currentLabel.clicked.connect(self.onCurrentLabelClick)
        self.powerLabel.clicked.connect(self.onPowerLabelClick)
        
    def onNewState(self):
        state = self.stateButton.isChecked()
        self.reactor.callInThread(self.setState, state)
    
    def onNewCurrent(self):
        current = self.currentBox.value()
        self.reactor.callInThread(self.setCurrent, current)

    def onNameLabelClick(self):
        self.reactor.callInThread(self.getAll)
    
    def onCurrentLabelClick(self):
        if QtGui.qApp.mouseButtons() & QtCore.Qt.LeftButton:
            self.reactor.callInThread(self.getCurrent)
        else:
            print 'relocking'
            self.reactor.callInThread(self.device.relock)

    def onPowerLabelClick(self):
        self.reactor.callInThread(self.getPower)
    
    def setState(self, state):
        self.device.state = state
        self.reactor.callFromThread(self.displayState, state)
        time.sleep(0.5)
        self.getPower()
    
    def setCurrent(self, current):
        self.device.current = current
        self.reactor.callFromThread(self.displayCurrent, current)
        time.sleep(0.2)
        self.getPower()

    def closeEvent(self, x):
        self.reactor.stop()

class MultipleClientContainer(QtGui.QWidget):
    name = None
    def __init__(self, client_list, reactor):
        QtGui.QDialog.__init__(self)
        self.client_list = client_list
        self.reactor = reactor
        self.populateGUI()
 
    def populateGUI(self):
        self.layout = QtGui.QHBoxLayout()
        for client in self.client_list:
            self.layout.addWidget(client)
        self.setFixedSize(210 * len(self.client_list), 140)
        self.setWindowTitle(self.name)
        self.setLayout(self.layout)

    def closeEvent(self, x):
        self.reactor.stop()
'''
if __name__ == '__main__':
    from current_controller3.devices.zs import DeviceProxy as ZSProxy

    class ZSClient(CurrentControllerClient):
        name = 'zs'
        DeviceProxy = ZSProxy
    
    from PyQt4 import QtGui
    app = QtGui.QApplication([])
    from client_tools import qt4reactor 
    qt4reactor.install()
    from twisted.internet import reactor

    widget = ZSClient(reactor)
    widget.show()
    reactor.run()
'''

