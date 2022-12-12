from PyQt4 import QtGui, QtCore, Qt
from PyQt4.QtCore import pyqtSignal 
import numpy as np
import json
import matplotlib
matplotlib.use('Qt4Agg')

class Spacer(QtGui.QFrame):
    def __init__(self, parent):
        super(Spacer, self).__init__(None)
        self.setFixedSize(parent.spacer_width, parent.spacer_height)
        self.setFrameShape(1)
        self.setLineWidth(0)


class SequencerButton(QtGui.QFrame):
    def __init__(self):
        super(SequencerButton, self).__init__(None)
        self.setFrameShape(2)
        self.setLineWidth(1)
        self.on_color = '#eeeeee'#ff69b4'
        self.off_color = '#fcfcfc'#ffffff'
    
    def setChecked(self, state):
        if state:
            self.setFrameShadow(0x0030)
            self.setStyleSheet('QWidget {background-color: %s}' % self.on_color)
            self.is_checked = True
        else:
            self.setFrameShadow(0x0020)
            self.setStyleSheet('QWidget {background-color: %s}' % self.off_color)
            self.is_checked = False

    def mousePressEvent(self, x):
        if self.is_checked:
            self.setChecked(False)
        else:
            self.setChecked(True)

class DigitalColumn(QtGui.QWidget):
    def __init__(self, channels, parent, position):
        super(DigitalColumn, self).__init__(None)
        self.channels = channels
        self.parent = parent
        self.position = position
        self.populate()

    def populate(self):
        self.buttons = {nl: SequencerButton() for nl in self.channels}
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        for i, nl in enumerate(sorted(self.channels, key=lambda nl: nl.split('@')[1])):
            if not i%16 and i != 0:
                self.layout.addWidget(Spacer(self.parent))
            self.layout.addWidget(self.buttons[nl])
            self.buttons[nl].on_color = self.parent.digital_colors[i%len(self.parent.digital_colors)]
        self.layout.addWidget(QtGui.QWidget())
        self.setLayout(self.layout)

    def getLogic(self):
        return {nl: int(self.buttons[nl].is_checked) for nl in self.channels}

    def setLogic(self, sequence):
        for nameloc in self.channels:
            self.buttons[nameloc].setChecked(sequence[nameloc][self.position]['out'])


class DigitalArray(QtGui.QWidget):
    def __init__(self, channels, parent):
        super(DigitalArray, self).__init__(None)
        self.channels = channels
        self.parent = parent
        self.populate()

    def populate(self):
        self.columns = [DigitalColumn(self.channels, self.parent, i) for i in range(self.parent.max_columns)]
        self.layout = QtGui.QHBoxLayout()
        for lc in self.columns:
            self.layout.addWidget(lc)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

    def displaySequence(self, sequence): 
        shown_columns = sum([1 for c in self.columns if not c.isHidden()])
        num_to_show = len(sequence[self.parent.timing_channel])
        if shown_columns > num_to_show:
            for c in self.columns[num_to_show: shown_columns][::-1]:
                c.hide()
        elif shown_columns < num_to_show:
            for c in self.columns[shown_columns:num_to_show]:
                c.show()
        for c in self.columns[:num_to_show]:
            c.setLogic(sequence)


class NameBox(QtGui.QLabel):
    clicked = QtCore.pyqtSignal()
    def __init__(self, nameloc, kw):
        super(NameBox, self).__init__(None)
        self.nameloc = nameloc
        name, loc = nameloc.split('@')
        self.setText(loc+': '+name)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter  )
        self.name = name
        self.off_color = '#eeeeee'#'#ffffff'
        self.auto_color = '#bbbbbb'
        self.on_color = '#eeeeee'#ffffff'
        self.mode = kw['mode']
        self.manual_output = kw['manual_output']
        self.updateDisplay()

    def mousePressEvent(self, x):
        self.clicked.emit()
    
    def updateMode(self, mode):
        self.mode = mode
        self.updateDisplay()

    def updateManualOutput(self, manual_output):
        self.manual_output = manual_output
        self.updateDisplay()

    def updateDisplay(self):
        if self.mode == 'manual':
            if self.manual_output:
                self.setStyleSheet('QWidget {background-color: %s}' % self.on_color)
            else:
                self.setStyleSheet('QWidget {background-color: %s}' % self.off_color)
        else:
            self.setStyleSheet('QWidget {background-color: %s}' % self.auto_color)

#    def displayModeState(self, x):
#        if x['mode'] == 'manual':
#            if x['manual_output']:
#                self.setStyleSheet('QWidget {background-color: %s}' % self.on_color)
#            else:
#                self.setStyleSheet('QWidget {background-color: %s}' % self.off_color)
#        else:
#            self.setStyleSheet('QWidget {background-color: %s}' % self.auto_color)
#

class DigitalNameColumn(QtGui.QWidget):
    def __init__(self, channels, parent):
        super(DigitalNameColumn, self).__init__(None)
        self.channels = channels
        self.parent = parent
        self.populate()

    def populate(self):
        self.labels = {k: NameBox(k, v) for k, v in self.channels.items()}
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(10, 0, 0, 0)
        for i, nl in enumerate(sorted(self.channels, key=lambda nl: nl.split('@')[1])):
            if not i%16 and i != 0:
                self.layout.addWidget(Spacer(self.parent))
            self.layout.addWidget(self.labels[nl])
            self.labels[nl].on_color = self.parent.digital_colors[i%len(self.parent.digital_colors)]
        self.layout.addWidget(QtGui.QWidget())
        self.setLayout(self.layout)

class DigitalClient(QtGui.QWidget):
    def __init__(self, channels, parent):
        super(DigitalClient, self).__init__(None)
        self.channels = channels
        self.parent = parent
        self.populate()

    def populate(self):
        self.nameColumn = DigitalNameColumn(self.channels, self.parent)
        self.nameColumn.scrollArea = QtGui.QScrollArea()
        self.nameColumn.scrollArea.setWidget(self.nameColumn)
        self.nameColumn.scrollArea.setWidgetResizable(True)
        self.nameColumn.scrollArea.setHorizontalScrollBarPolicy(1)
        self.nameColumn.scrollArea.setVerticalScrollBarPolicy(1)
        self.nameColumn.scrollArea.setFrameShape(0)

        self.array = DigitalArray(self.channels, self.parent)
        self.array.scrollArea = QtGui.QScrollArea()
        self.array.scrollArea.setWidget(self.array)
        self.array.scrollArea.setWidgetResizable(True)
        self.array.scrollArea.setHorizontalScrollBarPolicy(1)
        self.array.scrollArea.setVerticalScrollBarPolicy(1)
        self.array.scrollArea.setFrameShape(0)

        self.vscroll = QtGui.QScrollArea()
        self.vscroll.setWidget(QtGui.QWidget())
        self.vscroll.setHorizontalScrollBarPolicy(1)
        self.vscroll.setVerticalScrollBarPolicy(2)
        self.vscroll.setFrameShape(0)
        
        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.nameColumn.scrollArea)
        self.layout.addWidget(self.array.scrollArea)
        self.layout.addWidget(self.vscroll)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.connectWidgets()
    
    def displaySequence(self, sequence):
        self.array.displaySequence(sequence)

    def updateParameters(self, parameter_values):
        pass
    
    def connectWidgets(self):
        self.vscrolls = [self.nameColumn.scrollArea.verticalScrollBar(),
                self.array.scrollArea.verticalScrollBar(),
                self.vscroll.verticalScrollBar()]
        for vs in self.vscrolls:
            vs.valueChanged.connect(self.adjust_for_vscroll(vs))

    def adjust_for_vscroll(self, scrolled):
        def afv():
            val = scrolled.value()
            for vs in self.vscrolls:
                vs.setValue(val)
        return afv
