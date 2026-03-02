"""
Conductor parameter to generate advance table script for transports and send it to Moglabs XRF synthesizer
Not really parameter by itself; it loads other transport parameters, forms transport functon,
Generate advanced table script, and send it to the synthesizer at the beginning of each shot.
"""

# from labrad.server import LabradServer
from conductor.parameter import ConductorParameter
import os
import time
import json
import jsonplus

import numpy as np


class NoServerError(Exception):
    pass

class TransportXRFTableScriptGenerator(ConductorParameter):
    autostart = True
    priority = 3
    dev = None # dummy
    last_val = None # dummy
    
    # for building transports
    LATT_CONST = 813.4e-9/2 # m; lattice constant
    BASE_FREQ = 110e6 # Hz; base AOM drive frequence
    
    saveTableScript = True
    
    
    DEBUG_MODE = False
    # DEBUG_MODE = True
    def print_debug(self, str):
        if self.DEBUG_MODE is not True:
            return
        print("[DEBUG] " + str + "\n\tfrom " + __file__)
    
    def get_control_parameters(self, name):
        try:
            value = self.server.parameters[name].value
        except KeyError as ex:
            raise KeyError("Conductor parameter does not exist: {}".format(name), ex)
        except AttributeError as ex:
            raise AttributeError("Conductor parameter is not initialized: {}".format(name), ex)
        return value
    
    
    def initialize(self, config):
        """
        Called by conductor server when it starts up.
        See labrad_tool.conductor.parameter.ConductorParameter.__doc__
        """
        # initialize as a ConductorParameter instance
        # initialize() and also connect_to_labrad() in labrad_tool.conductor.parameter.ConductorParameter
        super(TransportXRFTableScriptGenerator, self).initialize(config)
        self.connect_to_labrad() # assign Labrad client in self.cxn
        
        # additional initialization for this parameter
        self.data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    
    
    def update(self):
        """
        Called (by conductor?) at the beginning of the each shot.
        See labrad_tool.conductor.parameter.ConductorParameter.__doc__
        """
        
        if self.value is None or self.value is False:
            self.print_debug('transport_xrf.update = {}; Skipping update...'.format(self.value))
            return
        
        # get experiment name & shot number of this shot
        exp_rel_path = self.server.experiment.get('name')
        shot_num = self.server.experiment.get('shot_number')
        self.print_debug('experiment name = {} (type={}), shot number = {} (type={})'.format(exp_rel_path, type(exp_rel_path), shot_num, type(shot_num)))
        if exp_rel_path is None or shot_num is None:
            self.print_debug('experiment name or shot number is None. Returning...')
            return
        
        # >>>>> identify transports in sequence >>>>>

        # get relevant parameter values for this shot
        try:
            update_shot = self.get_control_parameters('transport_xrf.update_shot')
            self.print_debug("Got update_shot = {}".format(update_shot))
            is_legacy_sequency = self.get_control_parameters('transport_xrf.legacy_mode')
            # sequence
            sequence = self.get_control_parameters('sequencer.sequence')
            self.print_debug("Got sequencer.sequence = {}".format(sequence))
            self.print_debug("type(sequence) = {}".format(type(sequence)))
            sequence = [str(subseq) for subseq in sequence] # convert unicode type to str type
            # XPARAM frequency control gain
            freq_gain = self.get_control_parameters('transport_xrf.freq_gain')
            # long transport
            form_long = self.get_control_parameters('transport_xrf.long_form')
            d_long = self.get_control_parameters('transport_xrf.long_distance')
            # t_long = self.get_control_parameters('transport_xrf.long_duration')
            t_long = self.get_control_parameters('sequencer.transport_xrf_long_duration')
            num_piece_long = self.get_control_parameters('transport_xrf.long_num_piece')
            self.print_debug("Got params long transport: form={}, x={}, d={}, num_piece={}".format(form_long, d_long, t_long, num_piece_long))
            # short transports
            form_short = self.get_control_parameters('transport_xrf.short_form')
            d_short = self.get_control_parameters('transport_xrf.short_distance')
            # t_short = self.get_control_parameters('transport_xrf.short_duration')
            t_short = self.get_control_parameters('sequencer.transport_xrf_short_duration')
            num_piece_short = self.get_control_parameters('transport_xrf.short_num_piece')
            #MM 20250617: adding tunable down distance
            d_short_down = self.get_control_parameters('transport_xrf.short_distance_down')
            self.print_debug("Got params for short trasports: form={}, d={}, t={}, num_piece={}".format(form_short, d_short, t_short, num_piece_short))
        except Exception as ex:
            if self.DEBUG_MODE:
                self.print_debug(ex.args[0])
            return
        
        
        # Update device only at the first shot if transport_xrf.update_shot is False
        if not update_shot:
            msg = "transport_xrf.update_shot is False "
            if shot_num > 0:
                msg += "and num_shot > 0. Skipping update..."
                self.print_debug(msg)
                return
            else:
                msg += "but num_shot = 0 (i.e., first shot). Continuing update..."
                self.print_debug(msg)

        
        # >>>>> form the sequence to send to the device server >>>>>
        if sequence is None:
            return
        
        is_transport_up_short = np.array([1 if "transport_short_up" in subseq else 0 for subseq in sequence])
        is_transport_down_short = np.array([1 if "transport_short_down" in subseq else 0 for subseq in sequence])
        # the sequence of up & down transports over this shot
        # up: +1, down: -1 (e.g, [+1, -1, -1, +1, ...])
        up_down_sequence_short = np.array([val for val in (is_transport_up_short - is_transport_down_short) if val != 0])
        up_down_sequence_short = list(up_down_sequence_short)
        self.print_debug("up_down_sequence_short={}".format(up_down_sequence_short))
        
        
        # # return inf there is no transport in the sequence
        # if len(up_dow_sequence_short) == 0:
        #     return
        
        # <<<<< form the sequence to send to the device server <<<<<
        
        
        # >>>>> generate table script  >>>>>
        
        self.print_debug("Generating table script...")
        
        transport_xrf_device_server = getattr(self.cxn, 'transport_xrf_device_server', None)
        if transport_xrf_device_server is None:
            self.last_val = self.value
            raise NoServerError("transport_xrf_device_server server is not found. Check the server status; is it on and running?")

        # send the transport_sequence to the device server
        request = {
            "is_legacy_transport": is_legacy_sequency,
            "freq_gain": freq_gain,
            "form_long": form_long,
            "d_long": d_long,
            "t_long": t_long,
            "num_piece_long": num_piece_long,
            "form_short": form_short,
            "d_short": d_short,
            "t_short": t_short,
            "num_piece_short": num_piece_short,
            "up_down_sequence_short": up_down_sequence_short,
            "d_short_down": d_short_down,
        }
        request_jsonplus = jsonplus.dumps(request)
        try:
            self.cxn.transport_xrf_device_server.update_transport(request_jsonplus)
        except Exception as ex:
            print("update() could not be called from transport_xrf_device_server. The server might be down. Refer to the following traceback.")
            self.last_val = self.value
            raise ex
        print "Lattice-transport Moglabs XRF synth updated."
        
        # <<<<< generate table script <<<<
        
        # assign value to this parameter
        # here it will be some useful information about the transport
        # self.value = {}
        self.last_val = self.value



Parameter = TransportXRFTableScriptGenerator

"""
Joon's note
Why not developing & using a labrad server, like PicoServer for picoscopes, to control Moglabs XRF synthesizer?
Is putting all the device controls (e.g., experiment-wise & shot-wise initializations, saving data) in this control parameter okay/sufficient? 
    - labrad_tool.conductor.parameter.ConductorParameter.__doc__ even suggests to do so.
    - cf. PicoSever's inheritance: 
        labrad.server.LabradServer (generic labrad server) >
        labrad_tools.server_tools.threaded_server.ThreadedSever (wrapper of LabradServer; related to threading) >
        labrad_tools.device_server.server.DeviceServer (generic labrad server for devices & have a list of all device servers (in `devices` class variable)) >
        labrad_tools.clock_pico.server.PicoServer (an implementation of the DeviceServer; what's used in exp!)

1. When experiment doesn't need to wait for the job
    The dedicated server will run such jobs ascynchronously from conductor
    In this case the time for initializing the synth is not a big concern,
    (Arming the synth (Receiving table script, parse it, & programming FPGA) few 10--100 ms sec typ.)
    It will be still nice to save some time and the synth will be armed while loading the blue MOT.
2. Python 3!
    The codes runing in the conductor must be python 2... I made a XRF server because of this.
"""
