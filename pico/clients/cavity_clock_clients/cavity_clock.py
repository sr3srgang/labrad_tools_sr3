import sys
import json
import time
import os
from shutil import copyfile
import numpy as np
from client_tools.connection3 import connection
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QDialog, QGridLayout, QMenu, QComboBox
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
import pico.clients.cavity_clock_clients.fits as fits
#from client_tools.connection import connection


class MplCanvas(FigureCanvas):
    def __init__(self):
        fig = plt.figure(figsize=(12, 16))
        self.fig = fig
        plt.rcParams.update({'font.size': 16, 'text.color': 'white'})
        # Set up subplots
        self.n_data_plots = 2
        gs = gridspec.GridSpec(ncols=self.n_data_plots*3, nrows=6)
        fig.patch.set_facecolor('black')
        self.trace_axes = [fig.add_subplot(
            gs[0:2, 1:5]), fig.add_subplot(gs[2:4, 0:3]), fig.add_subplot(gs[2:4, 3:6])]
        self.data_axes = [fig.add_subplot(gs[4:, i*3:(i + 1)*3])
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
        
        self.fig.set_tight_layout(True)
        FigureCanvas.__init__(self, self.fig)
        self.setFixedSize(1280, 960)
        
    def reset_data(self):
        self.data_x = [[] for _ in np.arange(self.n_data_plots)]
        self.data_y = [[] for _ in np.arange(self.n_data_plots)]
        [ax.clear() for ax in self.data_axes]
        


class CavityClockGui(QDialog):

    def __init__(self):
        super(CavityClockGui, self).__init__(None)
        self.update_id = np.random.randint(0, 2**31 - 1)
        self.expt= "Waiting for updates"
        self.data_path = None
        #Specify analysis frameworks
        self.analysis_script = fits.do_gaussian_fit
        self.mode = lambda update, preset : None
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
    

    def save_fig(self, ax, fig, title):
        #https://stackoverflow.com/questions/4325733/save-a-subplot-in-matplotlib
        extent = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        extent_expanded = extent.expanded(1.5, 2)
        fig.savefig(title, bbox_inches = extent_expanded)
        
                      
    def receive_update(self, c, update_json):
        update = json.loads(update_json)
        this_expt, this_path = listeners.get_expt(update)
        if this_expt is not None and self.expt != this_expt:
            if (not self.expt.isnumeric()) and (self.data_path is not None):
                #Save data traces when expt ends
                folder_path = os.path.join(self.data_path, self.expt)
                np.save(os.path.join(folder_path, "processed_data_x"), self.canvas.data_x)
                np.save(os.path.join(folder_path, "processed_data_y"), self.canvas.data_y)
                self.save_fig(self.canvas.data_axes[0], self.canvas.fig, os.path.join(folder_path, 'fig_0.png'))
                self.save_fig(self.canvas.data_axes[1], self.canvas.fig, os.path.join(folder_path, 'fig_1.png'))
                print('Saved data in folder: ' + folder_path)
            if this_expt.isnumeric():
                self.canvas.fig.suptitle(self.expt + " ended")
                self.expt = this_expt
            else:
                self.canvas.reset_data()
                self.expt = this_expt
                self.data_path = this_path
                self.canvas.fig.suptitle(self.expt)
                self.canvas.lim_set = self.canvas.lim_default
         
        #Get current lims to prevent re-scaling   
        lims = self.preserve_lim()
        preset = self.canvas.lim_set.copy()
        
        #Specify listeners for diff axes
        self.mode(update, preset)
        listeners.atom_number(update, self.canvas.data_axes[1], self.canvas.data_x[1], self.canvas.data_y[1], freq_domain = False)
        #self.mode(update, preset)
        

        '''
        try:
            returned, vrs_gnd = listeners.cavity_probe_two_tone(update, self.canvas.trace_axes[1]) 
            self.canvas.lim_set[1] = returned or preset[1]
            print('fit one')
            returned, vrs_exc = listeners.cavity_probe_two_tone(update, self.canvas.trace_axes[2], 'exc') 
            self.canvas.lim_set[2] = returned or preset[2]
            
            listeners.exc_frac_cavity(update, self.canvas.data_axes[1], self.canvas.data_x[1], self.canvas.data_y[1], vrs_gnd, vrs_exc, 'sequencer.clock_phase')
            
        except:
            print('cannot extract tones')
        
        '''      
        #Add back past lims to prevent rescaling
        self.enforce_lim(lims, preset)
        self.canvas.draw()



#Different potential plotter configs        
    def set_freq(self):
        def freq_update(update, preset):
            self.canvas.lim_set[0] = listeners.pmt_trace(update,self.canvas.trace_axes[0]) or preset[0]
            exc_called = listeners.exc_frac(update, self.canvas.data_axes[0], self.canvas.data_x[0], self.canvas.data_y[0])
        return freq_update

    def set_time(self, time_name):
        def time_update(update, preset):
            self.canvas.lim_set[0] = listeners.pmt_trace(update, self.canvas.trace_axes[0]) or preset[0]
            exc_called = listeners.exc_frac(update, self.canvas.data_axes[0], self.canvas.data_x[0], self.canvas.data_y[0], time_domain = True, time_name = time_name)    
        return time_update
 
                            
    def set_phase(self):
        def phase_update(update, preset):
            self.canvas.lim_set[0] = listeners.pmt_trace(update, self.canvas.trace_axes[0]) or preset[0]
            exc_called = listeners.exc_frac(update, self.canvas.data_axes[0], self.canvas.data_x[0], self.canvas.data_y[0], time_domain = True, time_name = 'sequencer.clock_phase')
        return phase_update
    

        
    def set_shot(self):
        def shot_update(update, preset):
            self.canvas.lim_set[0] = listeners.pmt_trace(update, self.canvas.trace_axes[0]) or preset[0]
            exc_called = listeners.exc_frac(update, self.canvas.data_axes[0], self.canvas.data_x[0], self.canvas.data_y[0], freq_domain = False, n_avg = 1)
                
        return shot_update



#Add buttons to select config, fit methods
     
    def add_subplot_buttons(self):
        self.nav.addAction('Fit', self.do_fit)
        
        #Add dropdown for setting data x axis
        self.dropdown = QComboBox(self)
        self.labels = ["Frequency", "Phase", "Dark time", "Pi time", "Shot num"]
        self.fxns = [self.set_freq(), self.set_phase(), self.set_time('sequencer.t_dark'), self.set_time('sequencer.t_pi'), self.set_shot()]
        self.dropdown.addItems(self.labels)
        self.dropdown.currentIndexChanged.connect(self.select_mode)
        self.dropdown.move(870, 4)
        self.mode = self.fxns[0]
        
        #Add dropdown for setting analysis fxn
        self.fxn_drop = QComboBox(self)
        self.fit_labels = ["Gaussian", "Inv. Gauss", "Phase fringe", "Local max", "Local min"]
        self.fit_fxns = [fits.do_gaussian_fit, fits.do_inverted_gaussian_fit, fits.do_phase_fit, fits.do_local_max, fits.do_local_min]
        self.fxn_drop.addItems(self.fit_labels)
        self.analysis_script = self.fit_fxns[0]
        self.fxn_drop.move(1000, 4)
        self.fxn_drop.currentIndexChanged.connect(self.select_script)
        
   
    def select_mode(self):
        txt = self.dropdown.currentText()
        ix = self.dropdown.currentIndex()
        self.mode = self.fxns[ix]
        self.canvas.reset_data()
        print(txt)
   
    def select_script(self):
        ix = self.fxn_drop.currentIndex()
        self.analysis_script = self.fit_fxns[ix]
                
    def do_fit(self):       
        self.analysis_script(self.canvas.data_axes[0], self.canvas.data_x[0], self.canvas.data_y[0])


