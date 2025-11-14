import json
import os
import numpy as np
from client_tools.connection3 import connection
from PyQt5.QtWidgets import QDialog, QGridLayout, QMenu, QComboBox, QPushButton, QLineEdit
from PyQt5.QtCore import QTimer, QDateTime
import data_analysis.imaging_tools as it
from twisted.internet.defer import inlineCallbacks

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import pico.clients.cavity_clock_clients.listeners as listeners
import pico.clients.cavity_clock_clients.fits as fits
# from client_tools.connection import connection

# >>>>> for InfluxDB uploader >>>>>
# from influxdb.helper import #validate_influxdb_uploader,\
from influxdb.helper import INFLUXDB_UPLOADER_SERVER_NAME, INFLUXDB_GET_EXPERIMENT_METHOD_NAME, \
    INFLUXDB_UPLOAD_METHOD_NAME, INFLUXDB_UPLOADER_TIMEOUT
from twisted.internet import reactor, defer
from twisted.internet.defer import Deferred, inlineCallbacks
import json
import traceback
import time
# <<<<< for InfluxDB uploader <<<<<


class MplCanvas(FigureCanvas):
    def __init__(self):
        fig = plt.figure(figsize=(24, 18))
        self.fig = fig
        self.fig.tight_layout()
        plt.rcParams.update({'font.size': 12, 'text.color': 'white'})
        # Set up subplots
        self.n_data_plots = 4
        gs = gridspec.GridSpec(ncols=25, nrows=18)
        fig.patch.set_facecolor('black')
        p_x = (1, 8)  # pmt row ixs
        c_x = (9, 16)  # cavity row ixs
        t_y = (1, 8)  # trace column ixs
        d1_y = (9, 16)
        d2_y = (17, 24)

        # fig.add_subplot(gs[2:4, 4:6]), fig.add_subplot(gs[2:4, 6:8])] #MM041322 switch to 2 trace, 1 data plot
        self.trace_axes = [fig.add_subplot(
            gs[x[0]:x[-1], t_y[0]:t_y[-1]]) for x in [p_x, c_x]]
        self.data_axes = [
            fig.add_subplot(gs[x[0]:x[-1], y[0]:y[-1]]) for x in [p_x, c_x] for y in [d1_y, d2_y]]

        self.lim_default = [False, False, False, False, False, False, False]
        self.lim_set = self.lim_default
        self.cav_snd_y = self.data_axes[2].twinx()

        self.all_ax = self.trace_axes + self.data_axes + [self.cav_snd_y]
        for ax in self.all_ax:
            ax.set_facecolor('xkcd:grey')
            ax.yaxis.label.set_color('white')
            ax.xaxis.label.set_color('white')
            ax.tick_params(color='white', labelcolor='white')

        # Initialize live data memory
        self.data_x = [[] for _ in np.arange(self.n_data_plots)]
        self.data_y = [[] for _ in np.arange(self.n_data_plots)]

        self.fig.set_tight_layout(True)
        FigureCanvas.__init__(self, self.fig)
        self.setFixedSize(1850, 1014)

    def reset_data(self):
        self.data_x = [[] for _ in np.arange(self.n_data_plots)]
        self.data_y = [[] for _ in np.arange(self.n_data_plots)]
        [ax.clear() for ax in self.data_axes]
        self.cav_snd_y.clear()


class CavityClockGui(QDialog):

    def __init__(self):
        super(CavityClockGui, self).__init__(None)
        self.update_id = np.random.randint(0, 2**31 - 1)
        self.expt = "Waiting for updates"
        self.data_path = None
        self.sweep = None
        self.seq = None
        # MM 20240203; save data and reset plotter every counter_thresh number of cavity shots processed
        self.shot_counter = 0
        self.save_counter = 0
        self.counter_thresh = 200
        # Specify analysis frameworks
        self.analysis_script = fits.do_gaussian_fit
        self.x_ax = None
        self.connect_to_labrad_cav()
        self.connect_to_labrad_clock()
        self.connect_to_labrad_conductor()

        self.populate()

    # Labrad connection:

    @inlineCallbacks
    def connect_to_labrad_cav(self):
        # self.cxn = connect(name=self.name)
        self.cxn = connection()
        # conductor = yield self.cxn.get_server('conductor')
        # print(conductor)
        # print(self.cxn.get_server('conductor'))
        yield self.cxn.connect(name='cavity viewer')
        # self.conductor_server = yield self.cxn.get_server('conductor')
        server = yield self.cxn.get_server('cavity_probe_pico')
        yield server.signal__update(self.update_id)
        yield server.addListener(listener=self.receive_update, source=None, ID=self.update_id)

        print('connected to cavity probe pico server')

    @inlineCallbacks
    def connect_to_labrad_clock(self):
        # self.cxn = connect(name=self.name)
        # self.cxn = connection()
        yield self.cxn.connect(name='clock viewer')
        server = yield self.cxn.get_server('clock_pico')
        yield server.signal__update(self.update_id)
        yield server.addListener(listener=self.receive_update, source=None, ID=self.update_id)
        print('connected to clock pico server')

    @inlineCallbacks
    def connect_to_labrad_conductor(self):
        yield self.cxn.connect(name='conductor pico client')
        conductor_server = yield self.cxn.get_server('conductor')
        # yield conductor_server.signal__update(self.update_id-1)
        yield conductor_server.addListener(listener=self.receive_update, source=None, ID=self.update_id-1)
        self.conductor_server = conductor_server
        self.influxdb_helper = yield self.cxn.get_server(INFLUXDB_UPLOADER_SERVER_NAME)

    def populate(self):
        self.setWindowTitle("Clock + cavity gui")
        self.canvas = MplCanvas()

        self.nav = NavigationToolbar(self.canvas, self)

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

    def preserve_lim(self):
        all_ax = self.canvas.all_ax
        lims = np.zeros((len(all_ax), 4))
        for i in np.arange(len(all_ax)):
            lims[i, 0:2] = all_ax[i].get_xlim()
            lims[i, 2:4] = all_ax[i].get_ylim()
        return lims

    def enforce_lim(self, lims, preset):
        all_ax = self.canvas.all_ax
        for i in np.arange(len(all_ax)):
            if preset[i]:
                all_ax[i].set_xlim(lims[i, 0:2])
                current_y = all_ax[i].get_ylim()
                if current_y[1] > lims[i, 3]:
                    lims[i, 3] = current_y[1]
                if current_y[0] < lims[i, 2]:
                    lims[i, 2] = current_y[0]
                all_ax[i].set_ylim(lims[i, 2:4])

    # @inlineCallbacks
    # def validate_influxdb_uploader(self):
    #     """
    #     Check if the InfluxDB uploader server and methods are available and
    #     return the availability.
    #     """
    #     # # if alabrad client is not given as argument, create one and return it
    #     # if cxn is None:
    #     #     cxn = labrad.connect()
    #     cxn = self.cxn

    #     is_available = False
    #     uploader_server = None
    #     get_current_experiment_info = None
    #     upload_experiment_shot = None
    #     try:
    #         print(f"[DEBUG] cxn = {cxn} ({type(cxn)})")
    #         uploader_server = yield cxn.get_server(INFLUXDB_UPLOADER_SERVER_NAME)
    #         uploader_server = getattr(cxn, INFLUXDB_UPLOADER_SERVER_NAME, None)
    #         if uploader_server is None:
    #             raise AttributeError(f"`{INFLUXDB_UPLOADER_SERVER_NAME}` server is not found. Check if the server is running.")
    #         get_current_experiment_info = getattr(uploader_server,INFLUXDB_GET_EXPERIMENT_METHOD_NAME, None)
    #         if get_current_experiment_info is None:
    #             raise AttributeError(f"`{INFLUXDB_GET_EXPERIMENT_METHOD_NAME}()` method in `{INFLUXDB_GET_EXPERIMENT_METHOD_NAME}` server is not found. Check if the server is running.")
    #         upload_experiment_shot = getattr(uploader_server, INFLUXDB_UPLOAD_METHOD_NAME, None)
    #         if upload_experiment_shot is None:
    #             raise AttributeError(f"`{INFLUXDB_UPLOAD_METHOD_NAME}()` method in `{INFLUXDB_GET_EXPERIMENT_METHOD_NAME}` server is not found. Check if the server is running.")
    #         is_available = True
    #     except:
    #         print("[WARN] Failed to connection to influxDB.")
    #         traceback.print_exc()
    #         print()

    #     # print(f"[DEBUG] InfluxDB uploader server is available: {is_available}\n"
    #     #         f"[DEBUG] \tuploader_server = {uploader_server}\n"
    #     #         f"[DEBUG] \tget_current_experiment_info = {get_current_experiment_info}\n"
    #     #         f"[DEBUG] \tupload_experiment_shot = {upload_experiment_shot}\n")
    #     return is_available, uploader_server, get_current_experiment_info, upload_experiment_shot

    @inlineCallbacks
    def receive_update(self, c, update_json):
        start_time = time.time()
        print(f"[DEBUG] {self.shot_counter}. receive_update() called.")
        update = json.loads(update_json)

        # >>>>> InfluxDB upload >>>>>
        # kick off getting the current experiment info before doing main tasks
        # is_influxdb_uploader_available, influxdb_uploader_server, \
        #     influxdb_get_current_experiment_info, influxdb_upload_experiment_shot = \
        #         validate_influxdb_uploader(self.cxn.cxn)
        # print(f"[DEBUG] is_influxdb_uploader_available = {is_influxdb_uploader_available}")

        # yield self.cxn.get_server(INFLUXDB_UPLOADER_SERVER_NAME)
        if False:
            uploader_server = self.influxdb_helper
            # get_current_experiment_info = getattr(uploader_server,INFLUXDB_GET_EXPERIMENT_METHOD_NAME, None)
            # upload_experiment_shot = getattr(uploader_server, INFLUXDB_UPLOAD_METHOD_NAME, None)

            is_influxdb_uploader_available = uploader_server is not None
            if is_influxdb_uploader_available:
                # experiment_info_d = uploader_server.get_current_experiment_info() # type: ignore
                # experiment_info_d.addTimeout(INFLUXDB_UPLOADER_TIMEOUT, reactor)
                experiment_info_json = yield uploader_server.get_current_experiment_info()
                experiment_info = json.loads(experiment_info_json)
                # experiment_info_list = [experiment_info[key] for key in ["exp_rel_path", "shot_num", "timestamp"]]
                print(f"[DEBUG] experiment_info = {experiment_info}")
        # <<<<< InfluxDB upload <<<<<
        influx_time = time.time()
        print('INFLUXDB ELAPSED TIME: {:.5f}'.format(influx_time-start_time))
        this_expt, this_path = listeners.get_expt(update)
        if this_expt is not None and (self.expt != this_expt or self.shot_counter >= self.counter_thresh):

            # MM updated 20241030 to save data when end expt is run, not just when a new expt starts
            # if (not self.expt.isnumeric()) and (self.data_path is not None):
            if (self.data_path is not None):
                # Save data traces when expt ends
                ix = self.save_counter
                folder_path = os.path.join(self.data_path, self.expt)
                np.save(os.path.join(folder_path, "processed_data_x_{}".format(ix)), np.asarray(
                    self.canvas.data_x, dtype=object), allow_pickle=True)
                np.save(os.path.join(folder_path, "processed_data_y_{}".format(ix)), np.asarray(
                    self.canvas.data_y, dtype=object), allow_pickle=True)
                # MM 20240304 saving just 1 fig showing full view
                self.canvas.fig.savefig(os.path.join(
                    folder_path, 'plotter_view_{}.png'.format(ix)))
                print('Saved data in folder: ' + folder_path)
                # MM 20241030
                if self.influxdb_params is not None:
                    listeners.log_to_influxdb(self.influxdb_params)
                self.save_counter += 1
                self.shot_counter = 0
                self.data_path = None

            if self.expt != this_expt:
                self.save_counter = 0

            if this_expt.isnumeric():
                self.canvas.fig.suptitle(self.expt + " ended")
                self.expt = this_expt
            else:
                print(this_expt)
                self.canvas.reset_data()
                self.expt = this_expt

                # MM 12142022 look for default warmup settings:

                keyword = 'warmup_'
                defaults = {'scan': 1, 'fixed': 0,
                            'flop': 4, 'sideband': 1, 'ramsey': 2}
                if keyword in this_expt:
                    expt_type = this_expt[len(keyword):this_expt.find('#')]
                    ix = defaults.get(expt_type)
                    if ix is not None:
                        self.x_ax = self.default_axes[ix]
                        self.dropdown.setCurrentIndex(ix)
                        self.select_mode()

                self.data_path = this_path
                self.canvas.fig.suptitle(self.expt)
                self.canvas.lim_set = self.canvas.lim_default
        ax_time = time.time()
        print(
            'AXIS/DATA MANAGE ELAPSED TIME: {:.5f}'.format(ax_time-influx_time))

        # Figure out cavity measurement parameters/sequences
        sweep, seq = listeners.sweep_params(update)
        if sweep is not None:
            self.sweep = sweep
        if seq is not None:
            self.seq = seq

        # MM 20241030: keep track of influxdb params, log once expt ends
        influxdb_params = listeners.get_influxdb_params(
            update, self.influxdb_log)
        if influxdb_params is not None:
            self.influxdb_params = influxdb_params
        select_params_time = time.time()
        print('SELECTED PARAM DIRECT UPLOAD: {:.5f}'.format(
            select_params_time-ax_time))
        # Get current lims to prevent re-scaling
        lims = self.preserve_lim()
        preset = self.canvas.lim_set.copy()

        #!!SPECIFY LISTENERS FOR DIFFERENT AXES
        # Comment/uncomment next lines to turn off/on pmt listeners:
        self.canvas.lim_set[0] = listeners.pmt_trace(
            update, self.canvas.trace_axes[0]) or preset[0]
        self.canvas.lim_set[2], x, n_g, n_e = listeners.pmt_atom_number(update, self.canvas.data_axes[0], self.canvas.data_x[0],
                                                                        self.canvas.data_y[0], ax_name=self.x_ax)
        self.canvas.lim_set[3] = listeners.pmt_exc_frac(
            self.canvas.data_axes[1], self.canvas.data_x[1], self.canvas.data_y[1], x, n_g, n_e)
        pmt_time = time.time()
        print(
            'PMT ELAPSED TIME: {:.5f}'.format(pmt_time - ax_time))

        # MM 041322 updating for homodyne listeners
        ran, datums, windows = listeners.filtered_cavity_time_domain(
            update, self.canvas.trace_axes[1], self.seq)
        cav_raw_time = time.time()
        print(
            'CAV TRACE ELAPSED TIME: {:.5f}'.format(cav_raw_time - pmt_time))
        if ran:
            self.shot_counter += 1
            processed_sweeps, x, dfs, DAC_voltage, shot_num = listeners.sweep_to_f(update, self.canvas.data_axes[2], self.canvas.cav_snd_y,
                                                                                   self.canvas.data_x[2], self.canvas.data_y[2], datums, self.sweep, windows, ax_name=self.x_ax)
            # self.canvas.lim_set[2] = True
            # MM added to save DAC voltage so conductor can find value:

            # yield self.cxn.get_server('conductor')
            server = self.conductor_server
            request = {"ram_servo.bare_dac_voltage": DAC_voltage}
            server.set_parameter_values(json.dumps(request))
            # yield server.set_parameter_values(json.dumps(request))

            # if self.data_path is not None:
            # folder_path = os.path.join(self.data_path, self.expt)
            # fname = os.path.join(folder_path,
            #                     "bare_dac_voltage_"+str(shot_num)+".txt")
            # with open(fname, 'w') as file:
            # file.write(str(DAC_voltage))
            # self.conductor_server.set_parameters(
            # json.dumps({'bare_dac_voltage': DAC_voltage}))
            # 'bare_dac_voltage').set_value(DAC_voltage)
            listeners.exc_frac_cavity(
                self.canvas.data_axes[3], self.canvas.data_x[3], self.canvas.data_y[3], x, dfs, windows)

        ram_servo_time = time.time()
        print(
            'UPLOAD BARE TO RAM SERVO TIME: {:.5f}'.format(ram_servo_time - cav_raw_time))
        # Add back past lims to prevent rescaling
        # self.enforce_lim(lims, preset)
        if ran:
            self.canvas.draw()
        final_time = time.time()
        print(
            'CAV EXC AND DRAW TIME: {:.5f}'.format(final_time - ram_servo_time))
        print('TOTAL TIME:{:.5f}'.format(final_time - start_time))

        # # >>>>> InfluxDB upload >>>>>
        # if is_influxdb_uploader_available:
        #     try:
        #         # get deferred experiment info return
        #         # experiment_info_json = yield experiment_info_d
        #         # experiment_info = json.loads(experiment_info_json)
        #         # experiment_info_list = [experiment_info[key] for key in ["exp_rel_path", "shot_num", "timestamp"]]
        #         # print(experiment_info)
        #         exp_rel_path = experiment_info["exp_rel_path"]
        #         shot_num = experiment_info["shot_num"]
        #         timestamp = experiment_info["timestamp"]
        #         # Configure and upload records
        #         measurement = "labrad_upload_server"
        #         tags = {}
        #         fields = {name: value for (name, value) in self.influxdb_params}
        #         fields_json = json.dumps(fields)
        #         print(f"[DEBUG] fields_json = {fields_json}")
        #         uploaded_from = f"receive_update()@cavity_clock.py"
        #         yield uploader_server.upload_experiment_shot(exp_rel_path, shot_num, timestamp, uploaded_from, json.dumps(fields_json), json.dumps(tags), measurement) # type: ignore
        #         print(f"[INFO] InfluxDB upload successful.")
        #     except defer.TimeoutError:
        #         print(f"[WARN] No reply from {INFLUXDB_UPLOADER_SERVER_NAME} in {INFLUXDB_UPLOADER_TIMEOUT} s – "
        #             "skipping upload.")
        #     except Exception as exc:
        #         print(f"[WARN] InfluxDB upload failed.")
        #         traceback.print_exc()
        # # <<<<<< InfluxDB upload <<<<<


# Add buttons to select config, fit methods

    def add_subplot_buttons(self):
        self.nav.addAction('Fit', self.do_fit)

        # MM 20240326
        # Add fill-in section for specifying arbitrary parameter for x axis
        self.param_box = QLineEdit(self)
        self.param_box.returnPressed.connect(self.specify_param)
        self.param_box.move(740, 4)
        # Add dropdown for setting data x axis
        self.dropdown = QComboBox(self)
        self.labels = ["Shot num", "Frequency",
                       "Phase", "Dark time", "Pi time", "specify param"]
        self.default_axes = [
            None, 'clock_sg380', 'sequencer.clock_phase', 'sequencer.t_dark', 'sequencer.t_pi', None]
        self.default_axes_labels = ["Shot num", 'Frequency (-116.55 MHz)',
                                    "Ramsey phase (2 pi rad)", "Dark time (s)", "Pi time (s)", "specified param"]
        # MM 20241030 specifying experimental params to log to influxdb
        self.influxdb_log = ['clock_pulse_sg380',
                             'cav_eom_amp_sg380', 'cav_eom_phase_sg380']

        self.dropdown.addItems(self.labels)
        self.dropdown.currentIndexChanged.connect(self.select_mode)
        self.dropdown.move(870, 4)

        # Add dropdown for setting analysis fxn
        self.fxn_drop = QComboBox(self)
        self.fit_labels = ["Gaussian", "Inv. Gauss",
                           "Phase fringe", "Local max", "Local min"]
        self.fit_fxns = [fits.do_gaussian_fit, fits.do_inverted_gaussian_fit,
                         fits.do_phase_fit, fits.do_local_max, fits.do_local_min]
        self.fxn_drop.addItems(self.fit_labels)
        self.analysis_script = self.fit_fxns[0]
        self.fxn_drop.move(1000, 4)
        self.fxn_drop.currentIndexChanged.connect(self.select_script)

    def specify_param(self):
        txt = self.param_box.displayText()
        if txt != "":
            self.default_axes[-1] = txt
            self.default_axes_labels[-1] = txt
            # MM 20241030: set to specify param whenever enter pressed
            ix = len(self.default_axes_labels) - 1
            self.dropdown.setCurrentIndex(ix)
            self.select_mode()

    def toggle_fit(self):
        self.do_fit = (self.do_fit + 1) % len(self.fit_settings)
        self.fit_toggle.setText(self.fit_settings[self.do_fit])

    def select_mode(self):
        # txt = self.dropdown.currentText()
        ix = self.dropdown.currentIndex()
        self.x_ax = self.default_axes[ix]
        self.canvas.reset_data()
        for ax in self.canvas.data_axes + [self.canvas.cav_snd_y]:
            ax.set_xlabel(
                self.default_axes_labels[ix], color='white')

    def select_script(self):
        ix = self.fxn_drop.currentIndex()
        self.analysis_script = self.fit_fxns[ix]

    def do_fit(self):
        try:
            self.analysis_script(
                self.canvas.data_axes[1], self.canvas.data_x[1], self.canvas.data_y[1])
        except:
            print(self.canvas.data_x[1], self.canvas.data_y[1])
        # MM 20240718
        self.analysis_script(
            self.canvas.data_axes[3], self.canvas.data_x[3], self.canvas.data_y[3])
