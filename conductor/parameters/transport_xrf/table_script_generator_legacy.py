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
    
    
    # DEBUG_MODE = False
    DEBUG_MODE = True
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
        
        # >>>>> identify transports in sequence >>>>>

        # get relevant parameter values for this shot
        try:
            # sequence
            sequence = self.get_control_parameters('sequencer.sequence')
            # long transport
            form_long = self.get_control_parameters('transport_xrf.long_form')
            x_long = self.get_control_parameters('transport_xrf.long_distance')
            d_long = self.get_control_parameters('transport_xrf.long_duration')
            # short transports
            form_short = self.get_control_parameters('transport_xrf.short_form')
            x_short = self.get_control_parameters('transport_xrf.short_distance')
            d_short = self.get_control_parameters('transport_xrf.short_duration')
        except Exception as ex:
            if self.DEBUG_MODE:
                self.print_debug(ex.args[0])
            return
        self.print_debug("Got sequence.value = {}".format(sequence))
        self.print_debug("Got params long transport: form={}, x={}, d={}".format(form_long, x_long, d_long))
        self.print_debug("Got params for short trasports: form={}, x={}, d={}".format(form_short, x_short, d_short))
        
        if sequence is None:
            return
        
        # 
        is_transport_up_short = np.array([1 if "transport_short_up" in subseq else 0 for subseq in sequence])
        is_transport_down_short = np.array([1 if "transport_short_down" in subseq else 0 for subseq in sequence])
        # the sequence of up & down transports over this shot
        # up: +1, down: -1 (e.g, [+1, -1, -1, +1, ...])
        up_down_sequence_short = np.array([val for val in is_transport_up_short - is_transport_down_short if val != 0])
        up_down_sequence_short = list(up_down_sequence_short)
        self.print_debug("up_down_sequence_short={}".format(up_down_sequence_short))
        
        # # return inf there is no transport in the sequence
        # if len(up_dow_sequence_short) == 0:
        #     return
        
        # >>>>> generate table script  >>>>>
        
        self.print_debug("Generating table script...")
        
        transport_xrf_device_server = getattr(self.cxn, 'transport_xrf_device_server', None)
        if transport_xrf_device_server is None:
            self.last_val = self.value
            raise NoServerError("transport_xrf_device_server server is not found. Check the server status; is it on and running?")

        # send the transport_sequence to the device server
        request = {
            "is_legacy_transport": True,
            "form_long": form_long,
            "x_long": x_long,
            "d_long": d_long,
            "form_short": form_short,
            "x_short": x_short,
            "d_short": d_short,
            "up_down_sequence_short": up_down_sequence_short,
        }
        request_jsonplus = jsonplus.dumps(request)
        try:
            self.cxn.transport_xrf_device_server.update(request_jsonplus)
        except Exception as ex:
            print("update() could not be called from transport_xrf_device_server. The server might be down. Refer to the following traceback.")
            self.last_val = self.value
            raise ex
        print "Lattice-transport Moglabs XRF synth updated."
        
        # <<<<< generate table script <<<<
        
        # assign value to this parameter
        # here it will be some useful information about the transport
        self.value = {}
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
