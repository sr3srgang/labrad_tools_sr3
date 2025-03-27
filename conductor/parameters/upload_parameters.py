"""
Conductor parameter to upload all the updated parameters (including itself)
Intended to have low priority (i.e., big priority value assigned) to be updated last in each shot
"""

# from labrad.server import LabradServer
from conductor.parameter import ConductorParameter
import json

class UploadParameters(ConductorParameter):

    autostart = True
    priority = 9999
    dev = None # dummy
    last_val = None # dummy
    
    # for building transports
    LATT_CONST = 813.4e-9/2 # m; lattice constant
    BASE_FREQ = 110e6 # Hz; base AOM drive frequence
    
    saveTableScript = True
    
    DEBUG_MODE = True
    def print_debug(self, msg):
        if self.DEBUG_MODE is not True:
            return
        print("[DEBUG] " + str(msg) + "\n\tfrom " + __file__, flush=True)
    
    
    def initialize(self, config):
        """
        Called by conductor server when it starts up.
        See labrad_tool.conductor.parameter.ConductorParameter.__doc__
        """
        self.print_debug('initializer() called.')
        
        # initialize as a ConductorParameter instance
        # initialize() and also connect_to_labrad() in labrad_tool.conductor.parameter.ConductorParameter
        super(UploadParameters, self).initialize(config)
        self.connect_to_labrad() # assign Labrad client in self.cxn
        
        # initalize as this class' object
        self.value = True # default value to record conductor parameters
        

    def update(self):
        """
        Called (by conductor server in _update_parameter() method) at the beginning of the each shot.
        See labrad_tool.conductor.parameter.ConductorParameter.__doc__
        """
        self.print_debug('update() called.')
        
        # Do not record conductor parameters if the value is not initialized, assigned, or False
        if not self.value:
            return
        if self.value is None or self.value is False:
            self.last_val = self.value
            return
        
        # get experiment name & shot number of this shot
        exp_rel_path = self.server.experiment.get('name')
        shot_num_str = self.server.experiment.get('shot_number')

        # relay sequencer.sequence parameter value of this shot
        parameters_json = self.cxn.conductor.get_parameter_values(request_json="{}", all=True)
        try:
            self.cxn.influxdb_uploader_server.upload_conductor_parameters(exp_rel_path, shot_num_str, parameters_json)
        except AttributeError as ex:
            print("'influxdb_uploader_server' server is not found. Check the server status; is it on and running?")

        # assign value to this parameter
        # here it will be some useful information about the transport
        # self.value = XX
        self.last_val = self.value



Parameter = UploadParameters