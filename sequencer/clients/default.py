import json
import time
import numpy as np
import os
import sys

from PyQt4 import QtGui, QtCore, Qt
from PyQt4.QtCore import pyqtSignal 
from twisted.internet.defer import inlineCallbacks

from client_tools.connection import connection
from client_tools.widgets import SuperSpinBox
from sequencer.clients.widgets.duration_widgets import DurationRow
from sequencer.clients.widgets.digital_widgets import DigitalClient
from sequencer.clients.widgets.analog_widgets import AnalogClient
from sequencer.clients.widgets.add_dlt_widgets import AddDltRow
from sequencer.clients.widgets.analog_editor import AnalogVoltageEditor
from sequencer.clients.widgets.analog_manual_client import AnalogVoltageManualClient
from sequencer.clients.helpers import merge_dicts, get_sequence_parameters, substitute_sequence_parameters

SEP = os.path.sep

class LoadAndSave(QtGui.QWidget):
    """ Tool bar for entering filenames, loading and saving """
    def __init__(self):
        super(LoadAndSave, self).__init__()
        self.populate()

    def populate(self):
        self.locationBox = QtGui.QLineEdit()
        self.loadButton = QtGui.QPushButton('Load')
        self.saveButton = QtGui.QPushButton('Save')
        self.layout = QtGui.QHBoxLayout()
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.layout.addWidget(self.locationBox)
        self.layout.addWidget(self.loadButton)
        self.layout.addWidget(self.saveButton)
        self.setLayout(self.layout)

class SequencerClient(QtGui.QWidget):
    name = None

    conductor_servername = None
    conductor_update_id = None
    sequencer_servername = None
    sequencer_update_id = None
    sequence_directory = None

    sequence_parameters = {}

    time_format = '%Y%m%d'

    spacer_width = 65
    spacer_height = 15
    namecolumn_width = 130
    namelabel_width = 200
    durationrow_height = 20
    analog_height = 50
    max_columns = 100
    digital_colors = ["#ff0000", "#ff7700", "#ffff00", "#00ff00", "#0000ff", "#8a2be2"]
    qt_style = 'Gtk+'

    def __init__(self, reactor, cxn=None):
        super(SequencerClient, self).__init__(None)
        self.sequencer_update_id = np.random.randint(0, 2**31 - 1)
        self.conductor_update_id = np.random.randint(0, 2**31 - 1)
        self.name = '{} - client'.format(self.sequencer_servername)
        self.reactor = reactor
        self.cxn = cxn
        self.connect()

    @inlineCallbacks
    def connect(self):
        try:
            if self.cxn is None:
                self.cxn = connection()  
                yield self.cxn.connect(name=self.name)
            yield self.getChannels()
            self.populate()
            yield self.displaySequence(self.default_sequence)
            yield self.connectSignals()
            yield self.getChannels()
#            yield self.get_sequence_parameters()
        except Exception, e:
            raise e

    @inlineCallbacks
    def getChannels(self):
        sequencer = yield self.cxn.get_server(self.sequencer_servername)
        channel_infos_json = yield sequencer.get_channel_infos()
        channel_infos = json.loads(channel_infos_json)
        self.channels = channel_infos
        self.analog_channels = {
                k: v
                    for device_name, device_channels in channel_infos.items()
                    for k, v in device_channels.items()
                    if v['channel_type'] == 'analog'
                }
        self.digital_channels = {
                k: v
                    for device_name, device_channels in channel_infos.items()
                    for k, v in device_channels.items()
                    if v['channel_type'] == 'digital'
                }

        self.default_sequence = dict(
            [(nameloc, [{'type': 'lin', 'vf': 0, 'dt': 1}]) 
                  for nameloc in self.analog_channels]
            + [(nameloc, [{'dt': 1, 'out': 0}]) 
                  for nameloc in self.digital_channels])
    
    def populate(self):
        self.loadAndSave = LoadAndSave()

        self.addDltRow = AddDltRow(self)
        self.addDltRow.scrollArea = QtGui.QScrollArea()
        self.addDltRow.scrollArea.setWidget(self.addDltRow)
        self.addDltRow.scrollArea.setWidgetResizable(True)
        self.addDltRow.scrollArea.setHorizontalScrollBarPolicy(1)
        self.addDltRow.scrollArea.setVerticalScrollBarPolicy(1)
        self.addDltRow.scrollArea.setFrameShape(0)

        self.durationRow = DurationRow(self)
        self.durationRow.scrollArea = QtGui.QScrollArea()
        self.durationRow.scrollArea.setWidget(self.durationRow)
        self.durationRow.scrollArea.setWidgetResizable(True)
        self.durationRow.scrollArea.setHorizontalScrollBarPolicy(1)
        self.durationRow.scrollArea.setVerticalScrollBarPolicy(1)
        self.durationRow.scrollArea.setFrameShape(0)
        
        self.digitalClient = DigitalClient(self.digital_channels, self)
        self.analogClient = AnalogClient(self.analog_channels, self)

        self.hscrollArray = QtGui.QScrollArea()
        self.hscrollArray.setWidget(QtGui.QWidget())
        self.hscrollArray.setHorizontalScrollBarPolicy(2)
        self.hscrollArray.setVerticalScrollBarPolicy(1)
        self.hscrollArray.setWidgetResizable(True)
        self.hscrollArray.setFrameShape(0)
        
        self.hscrollName = QtGui.QScrollArea()
        self.hscrollName.setWidget(QtGui.QWidget())
        self.hscrollName.setHorizontalScrollBarPolicy(2)
        self.hscrollName.setVerticalScrollBarPolicy(1)
        self.hscrollName.setWidgetResizable(True)
        self.hscrollName.setFrameShape(0)
        
        self.splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitter.addWidget(self.digitalClient)
        self.splitter.addWidget(self.analogClient)

        #spacer widgets
        self.northwest = QtGui.QWidget()
        self.northeast = QtGui.QWidget()
        self.southwest = QtGui.QWidget()
        self.southeast = QtGui.QWidget()

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.northwest, 0, 0, 2, 1)
        self.layout.addWidget(self.loadAndSave, 0, 1)
        self.layout.addWidget(self.northeast, 0, 2, 2, 1)
        self.layout.addWidget(self.durationRow.scrollArea, 1, 1)
        self.layout.addWidget(self.splitter, 2, 0, 1, 3)
        self.layout.addWidget(self.southwest, 3, 0, 1, 1)
        self.layout.addWidget(self.addDltRow.scrollArea, 3, 1)
        self.layout.addWidget(self.hscrollName, 4, 0)
        self.layout.addWidget(self.hscrollArray, 4, 1)
        self.layout.addWidget(self.southeast, 3, 2, 2, 1)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.setWindowTitle(self.name)

        self.setLayout(self.layout)
        self.setSizes()
        self.connectWidgets()

    def setSizes(self):
        self.northwest.setFixedSize(self.namecolumn_width, self.durationrow_height)
        self.loadAndSave.setFixedWidth(10*self.spacer_width)
        self.northeast.setFixedSize(20, self.durationrow_height)
        
        for c in self.digitalClient.array.columns:
            for b in c.buttons.values():
                b.setFixedSize(self.spacer_width, self.spacer_height)
            # -1 because there is a generic widget in the last spot
            height = sum([c.layout.itemAt(i).widget().height() for i in range(c.layout.count()-1)]) 
            c.setFixedSize(self.spacer_width, height)
        da_width = sum([c.width() for c in self.digitalClient.array.columns if not c.isHidden()])
        da_height = self.digitalClient.array.columns[0].height()
        self.digitalClient.array.setFixedSize(da_width, da_height)

        for nl in self.digitalClient.nameColumn.labels.values():
            nl.setFixedHeight(self.spacer_height)
        nc_width = self.namelabel_width
        nc_height = self.digitalClient.array.height()
        self.digitalClient.nameColumn.setFixedSize(nc_width, nc_height)
        self.digitalClient.nameColumn.scrollArea.setFixedWidth(self.namecolumn_width)
        
        self.digitalClient.vscroll.widget().setFixedSize(0, self.digitalClient.array.height())
        self.digitalClient.vscroll.setFixedWidth(20)
        
        width = self.digitalClient.array.width()
        height = self.analog_height*len(self.analog_channels)
        self.analogClient.array.setFixedSize(width, height)
        self.analogClient.vscroll.widget().setFixedSize(0, self.analogClient.array.height())
        self.analogClient.vscroll.setFixedWidth(20)
        
        for nl in self.analogClient.nameColumn.labels.values():
            nl.setFixedSize(self.namelabel_width, self.analog_height)
        nc_width = self.namelabel_width
        nc_height = self.analogClient.array.height()
        self.analogClient.nameColumn.setFixedSize(nc_width, nc_height)
        self.analogClient.nameColumn.scrollArea.setFixedWidth(self.namecolumn_width)
        
        for b in self.durationRow.boxes:
            b.setFixedSize(self.spacer_width, self.durationrow_height)
        dr_width = sum([db.width() for db in self.durationRow.boxes if not db.isHidden()])
        self.durationRow.setFixedSize(dr_width, self.durationrow_height)
        self.durationRow.scrollArea.setFixedHeight(self.durationrow_height)
       
        self.southwest.setFixedSize(self.namecolumn_width, self.durationrow_height)
        self.southeast.setFixedWidth(20)
        
        for b in self.addDltRow.buttons:
            b.setFixedSize(self.spacer_width, 15)
        self.addDltRow.setFixedSize(dr_width, self.durationrow_height)
        self.addDltRow.scrollArea.setFixedHeight(self.durationrow_height)
        
        self.hscrollArray.widget().setFixedSize(self.digitalClient.array.width(), 0)
        self.hscrollArray.setFixedHeight(20)
        self.hscrollName.widget().setFixedSize(self.namelabel_width, 0)
        self.hscrollName.setFixedSize(self.namecolumn_width, 20)

    def connectWidgets(self):
        self.hscrollArray.horizontalScrollBar().valueChanged.connect(self.adjustForHScrollArray)
        self.hscrollName.horizontalScrollBar().valueChanged.connect(self.adjustForHScrollName)

        self.loadAndSave.saveButton.clicked.connect(self.saveSequence)
        self.loadAndSave.loadButton.clicked.connect(self.browse)
#        self.loadAndSave.locationBox.returnPressed.connect(self.loadSequence)

        for i, b in enumerate(self.addDltRow.buttons):
            b.add.clicked.connect(self.addColumn(i))
            b.dlt.clicked.connect(self.dltColumn(i))

        for l in self.digitalClient.nameColumn.labels.values():
            l.clicked.connect(self.onDigitalNameClick(l.nameloc))

        for l in self.analogClient.nameColumn.labels.values():
            l.clicked.connect(self.onAnalogNameClick(l.nameloc))

    def adjustForHScrollArray(self):
        val = self.hscrollArray.horizontalScrollBar().value()
        self.durationRow.scrollArea.horizontalScrollBar().setValue(val)
        self.digitalClient.array.scrollArea.horizontalScrollBar().setValue(val)
        self.analogClient.array.scrollArea.horizontalScrollBar().setValue(val)
        self.addDltRow.scrollArea.horizontalScrollBar().setValue(val)
    
    def adjustForHScrollName(self):
        val = self.hscrollName.horizontalScrollBar().value()
        self.digitalClient.nameColumn.scrollArea.horizontalScrollBar().setValue(val)
        self.analogClient.nameColumn.scrollArea.horizontalScrollBar().setValue(val)
    
    def saveSequence(self):
        text = self.loadAndSave.locationBox.text()
        directory, filename = os.path.split(str(text))
        timestr = time.strftime(self.time_format)
        directory = self.sequence_directory.format(timestr)
        filepath = os.path.join(directory, filename)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(filepath, 'w') as outfile:
            sequence = self.getSequence()
            json.dump(sequence, outfile)
        self.loadAndSave.locationBox.setText(filepath)

    def browse(self):
        timestr = time.strftime(self.time_format)
        directory = self.sequence_directory.format(timestr)
        if not os.path.exists(directory):
            directory = self.sequence_directory.split('{}')[0]
        filepath = QtGui.QFileDialog().getOpenFileName(directory=directory)
        if filepath:
            self.loadAndSave.locationBox.setText(filepath)
            self.loadSequence(filepath)
    
    def loadSequence(self, filepath):
        with open(filepath, 'r') as infile:
            sequence = json.load(infile)
        master_sequence = sequence[self.master_channel]
        for board_key, board_info in self.channels.items():
            for channel_key, channel_info in board_info.items():
                channel_sequence = None
                matched_key = self.match_sequence_key(sequence, channel_key)
                if matched_key:
                    channel_sequence = sequence.pop(matched_key)
                if not channel_sequence:
                    if channel_key in self.analog_channels:
                        default_sequence_segment = [
                            {
                                'dt': s['dt'], 
                                'vf': channel_info['manual_output'],
                                'type': 'lin',
                                }
                            for s in master_sequence
                            ]
                    elif channel_key in self.digital_channels:
                        default_sequence_segment = [
                            {
                                'dt': s['dt'], 
                                'out': channel_info['manual_output'],
                                }
                            for s in master_sequence
                            ]
                sequence.update({channel_key: channel_sequence})

        self.displaySequence(sequence)
        self.loadAndSave.locationBox.setText(filepath)
    
    def match_sequence_key(self, channel_sequences, channel_key):
        channel_nameloc = channel_key.split('@') + ['']
        channel_name = channel_nameloc[0]
        channel_loc = channel_nameloc[1]

        for sequence_key, sequence in channel_sequences.items():
            sequence_nameloc = sequence_key.split('@') + ['']
            if sequence_nameloc == channel_nameloc:
                return sequence_key

        for sequence_key, sequence in channel_sequences.items():
            sequence_name = (sequence_key.split('@') + [''])[0]
            if sequence_name == channel_name:
                return sequence_key

        for sequence_key, sequence in channel_sequences.items():
            sequence_loc = (sequence_key.split('@') + [''])[1]
            if sequence_loc == channel_loc:
                return sequence_key
    
    @inlineCallbacks
    def displaySequence(self, sequence):
        self.sequence = sequence
        yield self.get_sequence_parameters()
        self.durationRow.displaySequence(sequence)
        self.digitalClient.displaySequence(sequence)
        self.analogClient.displaySequence(sequence)
        self.addDltRow.displaySequence(sequence)
        self.setSizes()

    def addColumn(self, i):
        def ac():
            sequence = self.getSequence()
            for board, channels in self.channels.items():
                for c in channels:
                    sequence[c].insert(i, sequence[c][i])
            self.displaySequence(sequence)
        return ac

    def dltColumn(self, i):
        def dc():
            sequence = self.getSequence()
            for board, channels in self.channels.items():
                for c in channels:
                    sequence[c].pop(i)
            self.displaySequence(sequence)
        return dc

    def onDigitalNameClick(self, channel_name):
        channel_name = str(channel_name)
        @inlineCallbacks
        def odnc():
            server = yield self.cxn.get_server(self.sequencer_servername)
            board_name = self.digital_channels[channel_name]['board_name']
            if QtGui.qApp.mouseButtons() & QtCore.Qt.RightButton:
                request = {board_name: {channel_name: None}}
                response_json = yield server.channel_modes(json.dumps(request))
                response = json.loads(response_json)
                if response[board_name][channel_name] == 'manual':
                    request = {board_name: {channel_name: 'auto'}}
                    yield server.channel_modes(json.dumps(request))
                else:
                    request = {board_name: {channel_name: 'manual'}}
                    yield server.channel_modes(json.dumps(request))
            elif QtGui.qApp.mouseButtons() & QtCore.Qt.LeftButton:
                request = {board_name: {channel_name: None}}
                response_json = yield server.channel_manual_outputs(json.dumps(request))
                response = json.loads(response_json)
                request = {board_name: {channel_name: not response[board_name][channel_name]}}
                yield server.channel_manual_outputs(json.dumps(request))
        return odnc

    def onAnalogNameClick(self, channel_name):
        channel_name = str(channel_name)
        channel_info = self.analog_channels[channel_name]
        @inlineCallbacks
        def oanc():
            if QtGui.qApp.mouseButtons() & QtCore.Qt.RightButton:

                class WidgetClass(AnalogVoltageManualClient):
                    name = channel_name
                    display_name = channel_name.split('@')[0]
                    sequencer_servername = self.sequencer_servername
                    board_name = channel_info.get('board_name')
                
                widget = WidgetClass(self.reactor, self.cxn, self)
                dialog = QtGui.QDialog()
                dialog.ui = widget
                dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
                widget.show()

            elif QtGui.qApp.mouseButtons() & QtCore.Qt.LeftButton:
                ave_args = (channel_name, self.getSequence(), self.cxn, self.reactor, self)
                ave = AnalogVoltageEditor(*ave_args)
                if ave.exec_():
                    sequence = ave.getEditedSequence().copy()
                    self.displaySequence(sequence)
                    conductor = yield self.cxn.get_server(self.conductor_servername)
                    yield conductor.signal__update(ave.conductor_update_id)
                    yield conductor.removeListener(listener=ave.receive_conductor_update, 
                                                   source=None, ID=ave.conductor_update_id)
        return oanc

    @inlineCallbacks
    def connectSignals(self):
        sequencer = yield self.cxn.get_server(self.sequencer_servername)
        yield sequencer.signal__update(self.sequencer_update_id)
        yield sequencer.addListener(listener=self.receive_sequencer_update, source=None,
                                    ID=self.sequencer_update_id)
        conductor = yield self.cxn.get_server(self.conductor_servername)
        yield conductor.signal__update(self.conductor_update_id)
        yield conductor.addListener(listener=self.receive_conductor_update, 
                                    source=None, ID=self.conductor_update_id)

    def updateParameters(self):
        yield None
        parameter_values = {}
        self.durationRow.updateParameters(parameter_values)
        self.digitalClient.updateParameters(parameter_values)
        self.analogClient.updateParameters(parameter_values)
        self.addDltRow.updateParameters(parameter_values)
        self.setSizes()

    def receive_sequencer_update(self, c, signal_json):
        signal = json.loads(signal_json)
        for message_type, message in signal.items():
            channel_manual_outputs = {}
            channel_modes = {}
            if message_type == 'channel_infos':
                channel_modes = {
                    k: v['mode']
                        for device_name, device_channels in message.items()
                        for k, v in device_channels.items()
                    }
                channel_manual_outputs = {
                    k: v['manual_output']
                        for device_name, device_channels in message.items()
                        for k, v in device_channels.items()
                    }
            if message_type == 'channel_manual_outputs':
                channel_manual_outputs = {
                    k: v
                        for device_name, device_channels in message.items()
                        for k, v in device_channels.items()
                    }
            elif message_type == 'channel_modes':
                channel_modes = {
                    k: v
                        for device_name, device_channels in message.items()
                        for k, v in device_channels.items()
                    }
            
            for k, v in channel_manual_outputs.items():
                if k in self.digital_channels:
                    label = self.digitalClient.nameColumn.labels[k]
                    label.updateManualOutput(v)
            for k, v in channel_modes.items():
                if k in self.digital_channels:
                    self.digitalClient.nameColumn.labels[k].updateMode(v)
    
    def receive_conductor_update(self, c, signal_json):
        signal = json.loads(signal_json)
        for message_type, message in signal.items():
            if message_type in ['set_parameter_values', 'get_parameter_values']:
                update = {
                    name.replace('sequencer.', '*'): value
                        for name, value in message.items()
                    }
                self.sequence_parameters.update(update)
                self.analogClient.displaySequence(self.sequence)
#                self.sequence_parameters.update(update)
#                self.analogClient.displaySequence(self.sequence)
    
    @inlineCallbacks
    def get_sequence_parameters(self):
        conductor = yield self.cxn.get_server(self.conductor_servername)
        parameter_names = get_sequence_parameters(self.sequence)
        request = {
            parameter_name.replace('*', 'sequencer.'): None
                for parameter_name in parameter_names
            }
        parameter_values_json = yield conductor.get_parameter_values(json.dumps(request))
        parameter_values = json.loads(parameter_values_json)
        self.sequence_parameters = {
            name.replace('sequencer.', '*'): value 
                for name, value in parameter_values.items()
            }

    def getSequence(self):
        durations = [b.value() for b in self.durationRow.boxes 
                if not b.isHidden()]
        digital_logic = [c.getLogic() 
                for c in self.digitalClient.array.columns 
                if not c.isHidden()]
        digital_sequence = {key: [{'dt': dt, 'out': dl[key]} 
                for dt, dl in zip(durations, digital_logic)]
                for key in self.digital_channels}
        analog_sequence = {key: [dict(s.items() + {'dt': dt}.items()) 
                for s, dt in zip(self.analogClient.sequence[key], durations)]
                for key in self.analog_channels}
        sequence = dict(digital_sequence.items() + analog_sequence.items())
        return sequence
    
#    def undo(self):
#        pass
#        #self.updateParameters()
#
#    def redo(self):
#        pass
#        #self.updateParameters()
#
#    def keyPressEvent(self, c):
#        super(SequencerClient, self).keyPressEvent(c)
#        if QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ClientModifier:
#            if c.key() == QtCore.Qt.Key_Z:
#                self.undo()
#            if c.key() == QtCore.Qt.Key_R:
#                self.redo()
#            if c.key() == QtCore.Qt.Key_S:
#                self.saveSequence()
#            if c.key() == QtCore.Qt.Key_Return:
#                self.runSequence(c)
#            if c.key() in [QtCore.Qt.Key_Q, QtCore.Qt.Key_W]:
#                self.reactor.stop()
#            if c.key() == QtCore.Qt.Key_B:
#                self.browse()
#
    def closeEvent(self, x):
        self.reactor.stop()

if __name__ == '__main__':
    a = QtGui.QApplication([])
    import client_tools.qt4reactor as qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = SequencerClient(reactor)
    widget.show()
    reactor.run()
