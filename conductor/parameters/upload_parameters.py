"""
Conductor parameter to upload all the updated parameters (including itself)
Intended to have low priority (i.e., big priority value assigned) to be updated last in each shot
"""

# from labrad.server import LabradServer
from conductor.parameter import ConductorParameter
import json

class UploadParameters(ConductorParameter):

    autostart = True
    priority = 999
    dev = None # dummy
    last_val = None # dummy
    
    DEBUG_MODE = False
    def print_debug(self, msg):
        if self.DEBUG_MODE is not True:
            return
        print "[DEBUG] " + str(msg) + "\n\tfrom " + __file__
    
    
    def initialize(self, config):
        """
        Called by conductor server when it starts up.
        See labrad_tool.conductor.parameter.ConductorParameter.__doc__
        """
        self.print_debug('initialize() called.')
        
        # initialize as a ConductorParameter instance
        # initialize() and also connect_to_labrad() in labrad_tool.conductor.parameter.ConductorParameter
        super(UploadParameters, self).initialize(config)
        self.connect_to_labrad() # assign Labrad client in self.cxn
        
        # # initalize as this class' object
        self.value = True # default value to record conductor parameters
        

    def update(self):
        """
        Called (by conductor server in _update_parameter() method) at the beginning of the each shot.
        See labrad_tool.conductor.parameter.ConductorParameter.__doc__
        """
        self.print_debug('update() called.')
        
        # Do not record conductor parameters if the value is not assigned or False
        if self.value != True:
            self.last_val = self.value
            return
        
        # get experiment name & shot number of this shot
        exp_rel_path = self.server.experiment.get('name')
        shot_num = self.server.experiment.get('shot_number')
        self.print_debug('experiment name = {} (type={}), shot number = {} (type={})'.format(exp_rel_path, type(exp_rel_path), shot_num, type(shot_num)))
        if exp_rel_path is None or shot_num is None:
            self.print_debug('experiment name or shot number is None. Skip uploading parameters.')
            self.last_val = self.value
            return
        
        # get influxdb_uploader_server
        # influxdb_uploader_server = self.cxn.influxdb_uploader_server
        servername = 'influxdb_uploader_server'
        influxdb_uploader_server = getattr(self.cxn, servername, None)
        if influxdb_uploader_server is None:
            self.last_val = self.value
            raise AttributeError("`{}` server is not found. Check the server status; is it on and running?".format(servername))

        # get all parameters of this shot from conductor server
        request_json="{}"; all=True
        parameters_json = self.cxn.conductor.get_parameter_values(request_json, all)
        self.print_debug('Got all parameters from conductor: \n' + parameters_json)
        
        # relay the parameter values to the influxdb_uploader_server.upload_conductor_parameters
        try:
            influxdb_uploader_server.upload_conductor_parameters(exp_rel_path, shot_num, parameters_json)
        except Exception as ex:
            print("update() could not be called from `{}` server. The server might be down. Refer to the following traceback.".format(servername))
            self.last_val = self.value
            raise ex
        
        print "Conductor parameters recorded in InfluxDB."
        self.print_debug('upload_conductor_parameters() in influxdb_uploader_server called.')
        
        # assign value to this parameter
        # here it will be some useful information about the transport
        # self.value = XX
        self.last_val = self.value



Parameter = UploadParameters