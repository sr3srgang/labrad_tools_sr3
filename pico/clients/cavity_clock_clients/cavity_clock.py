import sys
import json
import time
import os
from shutil import copyfile
import numpy as np
from client_tools.connection3 import connection
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QDialog, QGridLayout
from PyQt5.QtCore import QTimer, QDateTime
import data_analysis.imaging_tools as it
import warnings
from twisted.internet.defer import inlineCallbacks

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import pico.clients.cavity_clock_clients.listeners as listeners
#from client_tools.connection import connection


class MplCanvas(FigureCanvas):
    def __init__(self):
        fig = plt.figure(figsize=(12, 16))
        self.fig = fig
        plt.rcParams.update({'font.size': 16, 'text.color': 'white'})
        # Set up subplots
        self.n_data_plots = 2
        gs = gridspec.GridSpec(ncols=self.n_data_plots, nrows=5)
        fig.patch.set_facecolor('black')
        self.trace_axes = [fig.add_subplot(
            gs[0, :]), fig.add_subplot(gs[1, :]), fig.add_subplot(gs[2, :])]
        self.data_axes = [fig.add_subplot(gs[3:, i])
                          for i in np.arange(self.n_data_plots)]
        self.lim_default = [False, False, False, False, False, False]
        self.lim_set = self.lim_default
        for ax in self.trace_axes + self.data_axes:
            ax.set_facecolor('xkcd:grey')
            ax.yaxis.label.set_color('white')
            ax.xaxis.label.set_color('white')
            ax.tick_params(color='white', labelcolor='white')

        # Initialize live data memory
        self.data_x = [[] for _ in np.arange(self.n_data_plots)]
        self.data_y = [[] for _ in np.arange(self.n_data_plots)]
        # fig.suptitle('Hello')
        self.fig.set_tight_layout(True)
        FigureCanvas.__init__(self, self.fig)
        self.setFixedSize(1200, 900)
        
    def reset_data(self):
        self.data_x = [[] for _ in np.arange(self.n_data_plots)]
        self.data_y = [[] for _ in np.arange(self.n_data_plots)]
        [ax.clear() for ax in self.data_axes]
        


class CavityClockGui(QDialog):

    def __init__(self):
        super(CavityClockGui, self).__init__(None)
        self.update_id = np.random.randint(0, 2**31 - 1)
        self.add_fit = False
        self.expt= "Waiting for updates"
        self.connect_to_labrad_cav()
        self.connect_to_labrad_clock()
        self.populate()
        
        #self.Plotter = LivePlotter(self)

    def populate(self):
        self.setWindowTitle("Clock + cavity gui")
        self.canvas = MplCanvas()

        self.nav = NavigationToolbar(self.canvas, self)
        #self.nav.addAction('Select analysis method')
        #self.nav.addAction('Launch live plotter', self.launch_plotter)

        self.layout = QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.layout.addWidget(self.nav)
        self.layout.addWidget(self.canvas)

        self.setLayout(self.layout)
        width = self.canvas.width()
        height = self.nav.height() + self.canvas.height()
        self.setFixedSize(width, height)
        
        self.add_subplot_buttons()



    # Labrad connection:
    @inlineCallbacks
    def connect_to_labrad_cav(self):
        #self.cxn = connect(name=self.name)
        self.cxn = connection()
        yield self.cxn.connect(name='cavity viewer')
        server = yield self.cxn.get_server('cavity_probe_pico')
        yield server.signal__update(self.update_id)
        yield server.addListener(listener=self.receive_update, source=None, ID=self.update_id)
        print('connected to cavity probe pico server')

    @inlineCallbacks
    def connect_to_labrad_clock(self):
        #self.cxn = connect(name=self.name)
        self.cxn = connection()
        yield self.cxn.connect(name='clock viewer')
        server = yield self.cxn.get_server('clock_pico')
        yield server.signal__update(self.update_id)
        yield server.addListener(listener=self.receive_update, source=None, ID=self.update_id)
        print('connected to clock pico server')
        
    def preserve_lim(self):
        all_ax = self.canvas.trace_axes + self.canvas.data_axes
        lims = np.zeros((len(all_ax), 4))
        for i in np.arange(len(all_ax)):
            lims[i, 0:2] = all_ax[i].get_xlim()
            lims[i, 2:4] = all_ax[i].get_ylim()
        return lims
        
    def enforce_lim(self, lims, preset):
        all_ax = self.canvas.trace_axes + self.canvas.data_axes
        for i in np.arange(len(all_ax)):
            if preset[i]:
                all_ax[i].set_xlim(lims[i, 0:2])
                current_y = all_ax[i].get_ylim()
                if current_y[1] > lims[i, 3]:
                    lims[i, 3] = current_y[1]
                if current_y[0] < lims[i, 2]:
                    lims[i, 2] = current_y[0]
                all_ax[i].set_ylim(lims[i, 2:4])
    
    def freq_domain_config(self, update, preset):
        self.canvas.lim_set[0] = listeners.pmt_trace(update, self.canvas.trace_axes[0]) or preset[0]
        #try:
        exc_called = listeners.exc_frac(update, self.canvas.data_axes[0], self.canvas.data_x[0], self.canvas.data_y[0])
            #if exc_called:
             #   self.add_fit = False
        #except:
            #print('ERROR')
    
    def phase_fringe_config(self, update, preset):
        self.canvas.lim_set[0] = listeners.pmt_trace(update, self.canvas.trace_axes[0]) or preset[0]
        try:
            exc_called = listeners.exc_frac(update, self.canvas.data_axes[0], self.canvas.data_x[0], self.canvas.data_y[0], add_fit = self.add_fit, time_domain = True, time_name = 'sequencer.clock_phase')
            if exc_called:
                self.add_fit = False
        except:
            print('ERROR')
    
    def shot_num_config(self, update, preset):
        self.canvas.lim_set[0] = listeners.pmt_trace(update, self.canvas.trace_axes[0]) or preset[0]
        try:
            exc_called = listeners.exc_frac(update, self.canvas.data_axes[0], self.canvas.data_x[0], self.canvas.data_y[0], add_fit = self.add_fit, freq_domain = False)
            if exc_called:
                self.add_fit = False
        except:
            print('ERROR')
            
    
                    
    def receive_update(self, c, update_json):
        update = json.loads(update_json)
        #print(update)
        this_expt = listeners.get_expt(update)
        if this_expt is not None and self.expt != this_expt:
            if this_expt.isnumeric():
                self.canvas.fig.suptitle(self.expt + " ended")
                self.expt = this_expt
            else:
                self.canvas.reset_data()
                self.expt = this_expt
                self.canvas.fig.suptitle(self.expt)
                self.canvas.lim_set = self.canvas.lim_default
         
        #Get current lims to prevent re-scaling   
        lims = self.preserve_lim()
        preset = self.canvas.lim_set.copy()
        
        #Specify listeners for diff axes
        #if 'sideband_scan' in this_expt:
        self.freq_domain_config(update, preset)
        #self.rabi_flop_config(update, preset)
        #self.phase_fringe_config(update, preset)
        #self.canvas.lim_set[0] = listeners.pmt_trace(update, self.canvas.trace_axes[0]) or preset[0]
        
        #try:
        #self.canvas.lim_set[1] = listeners.cavity_probe_two_tone(update, self.canvas.trace_axes[1]) or preset[1]
        #self.canvas.lim_set[2] = listeners.cavity_probe_two_tone(update, self.canvas.trace_axes[2], 'exc') or preset[2]
        #except:
        #    print('hellooo')
            #self.canvas.lim_set[1] = False
        #else:    
        #self.canvas.lim_set[0] = listeners.pmt_trace(update, self.canvas.trace_axes[0]) or preset[0]
        #listeners.exc_frac(update, self.canvas.data_axes[1], self.canvas.data_x[1], self.canvas.data_y[1], 
        #freq_domain = False, add_fit = False)
              
        #Add back past lims to prevent rescaling
        self.enforce_lim(lims, preset)
        self.canvas.draw()

    def add_subplot_buttons(self):
        self.nav.addAction('Fit', self.do_fit)
    
    def do_fit(self):
        listeners.do_gaussian_fit(self.canvas.data_axes[0], self.canvas.data_x[0], self.canvas.data_y[0])
        
    def enable_fit(self):
        self.add_fit = True
        print('Will fit on next shot')
        self.canvas.draw()
'''
Old listener scrap       
        try:
            self.canvas.lim_set[1] = listeners.cavity_probe_two_tone(update, self.canvas.trace_axes[1]) or preset[1]
        except:
            self.canvas.lim_set[1] = False
        #try:
        exc_called = listeners.exc_frac(update, self.canvas.data_axes[0], self.canvas.data_x[0], self.canvas.data_y[0], add_gauss = self.add_gauss)
        if exc_called:
            self.add_gauss = False
        #except:
        #    print('ERROR')
        #listeners.exc_frac(update, self.canvas.data_axes[1], self.canvas.data_x[1], self.canvas.data_y[1], time_domain = True, time_name= 'sequencer.clock_phase')      

'''  

'''
    def receive_update(self, c, update_json):
        update = json.loads(update_json)
        for key, value in update.items():
            if key == self.camera:
                if self.fluorescence_mode:
                    if not (('exc' in value[0]) or ('background' in value[0])):
                        print(value)
                        if 'gnd' in value[0]:
                            str_end = '_fluorescence.png'
                            keyword = 'fluor_'
                            split_str = value[0].partition(str_end)
                            parse_name = split_str[0].partition(keyword)
                            beginning = parse_name[0]
                            shot_num = int(parse_name[-1])
                            offset = 3
                            mod_shot = shot_num - offset
                            new_path = beginning + keyword + \
                                str(mod_shot) + str_end
                            print(new_path)
                            self.file_to_show = new_path#value[0]
                        else:
                            self.file_to_show = value[0]

                        self.Plotter.show_window()
                        self.show_window()
 '''
