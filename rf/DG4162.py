## low-level codes for communication with & control RIGOL DG4162 AWGs

class FrequencyOutOfBoundsError(Exception):
    pass

class AmplitudeOutOfBoundsError(Exception):
    pass


class DG4162(object):
    _frequency_range = (1e-3, 160e6)  # Min: 1 mHz, Max: 160 MHz
    _vxi11_address = None
    is_vervose = True

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if 'vxi11' not in globals():
            global vxi11
            import vxi11
        self._inst = vxi11.Instrument(self._vxi11_address)
        
        # call function to define channelwise control parameters as object properties
        self.define_props_ch_params()
        
    # helper methods intended to be "protected"
    
    def print_verbose(self, msg):
        if self.is_vervose:
            msg = "RIGOL {}: {}.".format(self._vxi11_address, msg)
            print(msg)
        

    def _validate_freq_input(self, frequency):
        """
        Check if a input frequency is valid for this device (range & resolution) and
        raise errors or warnings and/or return an appropriate valid frequency value.
        """
        # check range
        if frequency < min(self._frequency_range) or frequency > max(self._frequency_range):
            raise FrequencyOutOfBoundsError(frequency)
        
        # check resolution
        if frequency*100 % 1 != 0: # not integer mHz
            print("WARNING: RIGOL DG4162 frequency can be set to integer mHz! Your input %f Hz is rounded to %.03f Hz" % (frequency, frequency))
            frequency = round(frequency, 3)
        
        # return valid frequency inputS
        return frequency

    def _validate_sweep_time_input(self, t):
        #TBD
        return t
    
    def _validate_sweep_hold_time_input(self, t):
        #TBD
        return t
    
    # global (i.e., non-channel-wise) control
    def align_phase(self):
        command = ':SOURce1:PHASe:INITiate; :SOURce2:PHASe:INITiate'
        self._inst.write(command)
        self.print_verbose('Phase aligned.')
        
    def set_local(self):
        command = 'SYSTem:LOCal'
        self._inst.write(command)
        self.print_verbose('Set to local control mode.')    
    
    # general getter & setter for channal-wise control parameters
    # (i.e., SCPI commands starting with ':SOURce1:' or ':SOURce2:')
    # 'command' argument should replace channel number to curly brackets 
    # (e.g, ':SOURce1:FREQuency:START' to ':SOURce{}:FREQuency:START')
    
    def _get_ch_param(self, param_name, command, chinx):
        command = command.format(chinx)
        command = command + '?'
        ans = self._inst.ask(command)
        msg = "channel {} {} queried.".format(chinx, param_name) \
                + "\n\tcommand: {}".format(command) \
                + "\n\tresponse: {}".format(ans)
        self.print_verbose(msg)
        return float(ans)
    def _set_ch_param(self, param_name, command, chinx, value):
        command = command.format(chinx)
        command = command + ' {}'.format(value)
        msg = "channel {} {} set to {}.".format(chinx, param_name, value) \
                + "\n\tcommand: {}".format(command)                                                                               
        self.print_verbose(msg)
        self._inst.write(command)
    
    
    # define getter & setters for specific channelwise control parameters
    # by wrapping the using the above generic getter & setters
    # unit of values are Hz, s, or dBm
    commands_ch_param = {} # dict that store channelwise control parameter names (as keys) and the associated SCPI commands (as values)
    
    commands_ch_param['sweep_start_frequency'] = "SOURce{}:FREQuency:STARt"
    def get_sweep_start_frequency(self, chinx):
        param_name = 'sweep_start_frequency'
        return self._get_ch_param(param_name=param_name, command=self.commands_ch_param[param_name], chinx=chinx)
    def set_sweep_start_frequency(self, chinx, frequency):
        param_name = 'sweep_start_frequency'
        frequency = self._validate_freq_input(frequency)
        return self._set_ch_param(param_name=param_name, command=self.commands_ch_param[param_name], chinx=chinx, value=frequency)
    
    commands_ch_param['sweep_stop_frequency'] = "SOURce{}:FREQuency:STOP"
    def get_sweep_stop_frequency(self, chinx):
        param_name = 'sweep_stop_frequency'
        return self._get_ch_param(param_name=param_name, command=self.commands_ch_param[param_name], chinx=chinx)
    def set_sweep_stop_frequency(self, chinx, frequency):
        param_name = 'sweep_stop_frequency'
        frequency = self._validate_freq_input(frequency)
        return self._set_ch_param(param_name=param_name, command=self.commands_ch_param[param_name], chinx=chinx, value=frequency)
        
    commands_ch_param['sweep_time'] = ":SOURce{}:SWEep:TIME"
    def get_sweep_time(self, chinx):
        param_name = 'sweep_time'
        return self._get_ch_param(param_name=param_name, command=self.commands_ch_param[param_name], chinx=chinx)
    def set_sweep_time(self, chinx, t):
        param_name = 'sweep_time'
        t = self._validate_sweep_time_input(t)
        return self._set_ch_param(param_name=param_name, command=self.commands_ch_param[param_name], chinx=chinx, value=t)
        
    commands_ch_param['sweep_hold_time'] = ":SOURce{}:SWEep:HTIMe:STOP"
    def get_sweep_hold_time(self, chinx):
        param_name = 'sweep_hold_time'
        return self._get_ch_param(param_name=param_name, command=self.commands_ch_param[param_name], chinx=chinx)
    def set_sweep_hold_time(self, chinx, t):
        param_name = 'sweep_hold_time'
        t = self._validate_sweep_hold_time_input(t)
        return self._set_ch_param(param_name=param_name, command=self.commands_ch_param[param_name], chinx=chinx, value=t)
    
    commands_ch_param['sweep_return_time'] = ":SOURce{}:SWEep:RTIMe"
    def get_sweep_return_time(self, chinx):
        param_name = 'sweep_return_time'
        return self._get_ch_param(param_name=param_name, command=self.commands_ch_param[param_name], chinx=chinx)
    def set_sweep_return_time(self, chinx, t):
        param_name = 'sweep_return_time'
        t = self._validate_sweep_time_input(t)
        return self._set_ch_param(param_name=param_name, command=self.commands_ch_param[param_name], chinx=chinx, value=t)

    
    # define the control parameters above of each RIGOL channel as an object property (using `property` decorator)
    # usage: 
    # value = <DG4162 object>.sweep_start_frequency[chinx] # get
    # <DG4162 object>.sweep_start_frequency[chinx] = value # set
    # where `chinx`` is the channel index (1 for CH1 and 2 for CH2 of the device) 
    class ChParamPropertyList:
        CHNUM = 2 # channel # of the device
        def __init__(self, getter, setter):
            self._getter = getter  # Function to get value
            self._setter = setter  # Function to set value

        def __getitem__(self, chinx):
            """Retrieve the property value"""
            if chinx < 1 or chinx > self.CHNUM:
                raise IndexError("RIGOL DG4162 Channel index out of range")
            return self._getter(chinx)

        def __setitem__(self, chinx, value):
            """Set the property value"""
            if chinx < 1 or chinx > self.CHNUM:
                raise IndexError("RIGOL DG4162 Channel index out of range")
            self._setter(chinx, value)
            
    def define_props_ch_params(self):
        self.sweep_start_frequency = self.ChParamPropertyList(self.get_sweep_start_frequency, self.set_sweep_start_frequency)
        self.sweep_stop_frequency = self.ChParamPropertyList(self.get_sweep_stop_frequency, self.set_sweep_stop_frequency)
        self.sweep_time = self.ChParamPropertyList(self.get_sweep_time, self.set_sweep_time)
        self.sweep_hold_time = self.ChParamPropertyList(self.get_sweep_hold_time, self.set_sweep_hold_time)
        self.sweep_return_time = self.ChParamPropertyList(self.get_sweep_return_time, self.set_sweep_return_time)

       
    # @property
    # def sweep_stop_frequency_ch1(self):
    #     return self.get_sweep_stop_frequency(1)
        
    # @sweep_stop_frequency_ch1.setter
    # def sweep_stop_frequency_ch1(self, frequency):
    #     self.set_sweep_stop_frequency(1, frequency)
    
    # @property
    # def sweep_stop_frequency_ch2(self):
    #     return self.get_sweep_stop_frequency(2)
        
    # @sweep_stop_frequency_ch2.setter
    # def sweep_stop_frequency_ch2(self, frequency):
    #     self.set_sweep_stop_frequency(2, frequency)
    
        

        
        

       
class DG4162Proxy(DG4162):
    _vxi11_servername = None

    def __init__(self, cxn=None, **kwargs):
        if cxn == None:
            import labrad
            cxn = labrad.connect()
        from vxi11_server.proxy import Vxi11Proxy
        global vxi11
        vxi11 = Vxi11Proxy(cxn[self._vxi11_servername])
        SG380.__init__(self, **kwargs)




