"""
Conductor parameter to generate and save small transports sequence using Moglabs XRF synthesizer
"""

# from labrad.server import LabradServer
from conductor.parameter import ConductorParameter
import os
import time
import numpy as np


class TransportXRFSmallTransportSequence(ConductorParameter):
    autostart = True
    priority = 2
    dev = None # dummy
    last_val = None # dummy
    
    
    DEBUG_MODE = False
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
        super(TransportXRFSmallTransportSequence, self).initialize(config)
        self.connect_to_labrad() # assign Labrad client in self.cxn
        
        # additional initialization for this parameter
        # pass
    
    
    def update(self):
        """
        Called (by conductor?) at the beginning of the each shot.
        See labrad_tool.conductor.parameter.ConductorParameter.__doc__
        """
        
        self.value = None # value in case the transport sequence generation is failed.
        self.last_val = self.value
        
        # >>>>> identify transports in sequence >>>>>
        
        # get sequencer.sequence parameter value of this shot
        try:
            sequence = self.get_control_parameters('sequencer.sequence')
        except Exception as ex:
            if self.DEBUG_MODE:
                self.print_debug(ex.args[0])
            return
        self.print_debug("sequence.value={}".format(sequence))
        if sequence is None:
            return
        
        
        # previous_sequence = ConductorParameter.server.parameters.get( # related to one-shot lag..?
        #     'sequencer.previous_sequence') 
        is_transport_up = np.array([1 if "transport_small_up" in subseq else 0 for subseq in sequence])
        is_transport_down = np.array([1 if "transport_small_down" in subseq else 0 for subseq in sequence])
        # the sequence of up & down transports over this shot
        # up: +1, down: -1 (e.g, [+1, -1, -1, +1, ...])
        up_down_sequence = np.array([val for val in is_transport_up - is_transport_down if val != 0])
        self.print_debug("up_down_sequence={}".format(up_down_sequence))
        
        # return if there is no transport in the sequence
        if len(up_down_sequence) == 0:
            return
        
        # <<<<< identify transports in sequence <<<<<
        


        # >>>>> generate transport sequence  >>>>>
        
        # get relevant parameter values in this shot
        try:
            form = self.get_control_parameters('transport_xrf.small_form')
            x = self.get_control_parameters('transport_xrf.small_distance')
            d = self.get_control_parameters('transport_xrf.small_duration')
        except Exception as ex:
            if self.DEBUG_MODE:
                self.print_debug(ex.args[0])
            return
        self.print_debug("Got conductor parameters form={}, x={}, d={}".format(form, x, d))
        if form is None or x is None or d is None:
            return

        transport_sequence = []
        try:
            # pre-defined transport form
            self.print_debug("type(form)={}".format(type(form)))
            if isinstance(form, (str, unicode)):
                form = str(form)
                for val in up_down_sequence:
                    segment = (d, form, val*x)
                    transport_sequence.append(segment)
                    transport_sequence.append('t') # trigger between transports
            else:
                # custom sequence; ignore x and d
                for key, value in form.items():
                    if isinstance(value, tuple):
                        # segment; change to a one-segment sequence
                        form[key] = [value]
                
                for val in up_down_sequence:
                    sequence = form["up" if val == 1 else "down"] # assign given custom up or down sequence
                    # if ... check type, length, data type of each segment
                    transport_sequence.append(sequence)
                    transport_sequence.append('t') # trigger between transports

        except KeyError as ex:
            pass
        except ValueError as ex:
            pass
        
        transport_sequence = transport_sequence[0:-1] # drop the last trigger
        self.print_debug("transport_sequence generated: {}".format(transport_sequence))
        
        
        # <<<<< generate transport sequence <<<<<
        
        self.value = transport_sequence
        self.last_val = self.value


Parameter = TransportXRFSmallTransportSequence

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
