"""
Conductor parameter to set small transport sweep frequency "amplitude" in Hz.
It sets the sweep stop frequencies of RIGOL channels for transport up and down,
antisymmetically by the same magnitude, from the given carrier frequencies
(in `sweep_start_frequency_up` & `sweep_start_frequency_down` variables).
"""

from conductor.parameter import ConductorParameter
import os
from rf.DG4162 import *
from influxdb.influxdb_write_py27 import *

class TransportSmallDG4162SweepAmplitude(ConductorParameter):
    autostart = True
    priority = 4
    dev_up = None
    dev_down = None
    last_val = None
    sweep_start_frequency_up = 31e6
    sweep_start_frequency_down = 19e6

    def initialize(self, config):
        super(TransportSmallDG4162SweepAmplitude, self).initialize(config)
        self.connect_to_labrad()
        self.param_name = os.path.splitext(os.path.basename(__file__))[0]
        self.dev_up = DG4162(_vxi11_address = "192.168.1.43", is_vervose = False); self.chinx_up = 1 # VLATT RIGOL 3 CH1 for transport up
        self.dev_down = DG4162(_vxi11_address = "192.168.1.42", is_vervose = False); self.chinx_down = 1 # VLATT RIGOL 2 CH1 for transport down
        
        self.update()
        
        
    def update(self):
        isUpdated = False
        
        if self.value is not None:
            isUpdated = True
            # if self.value != self.last_val:
            self.dev_up.sweep_stop_frequency[self.chinx_up] = self.sweep_start_frequency_up + self.value
            self.dev_down.sweep_stop_frequency[self.chinx_down] = self.sweep_start_frequency_down - self.value
            # print(self.param_name + " is " + str(self.value))
            # self.dev_up.set_local()
            # self.dev_down.set_local()
            self.last_val = self.value
        
        # update other values together to the device
        # # sweep & return time
        param_name = 'transport_small_sweep_time_dg4162'
        param = self.server.parameters.get(param_name)
        if param is not None:
            t = param.value
            if t is not None:
                isUpdated = True
                # sweep time
                self.dev_up.sweep_time[self.chinx_up] = t
                self.dev_down.sweep_time[self.chinx_down] = t
                # sweep return time
                self.dev_up.sweep_return_time[self.chinx_up] = t
                self.dev_down.sweep_return_time[self.chinx_down] = t
                # print(param_name + " is " + str(t))
        
        # # sweep hold time
        param_name = 'transport_small_sweep_hold_time_dg4162'
        param = self.server.parameters.get(param_name)
        if param is not None:
            t = param.value
            if t is not None:
                self.dev_up.sweep_hold_time[self.chinx_up] = t
                self.dev_down.sweep_hold_time[self.chinx_down] = t
                # print(param_name + " is " + str(t))
            
        if isUpdated is True:
            self.dev_up.set_local()
            self.dev_down.set_local()
            
        self.upload_influxdb()
            
    def upload_influxdb(self):
        """Upload relevant values to InfluxDB"""
        fields = {}
        
        # transport_small_sweep_amp_dg4162
        if self.value is not None:
            fields[self.param_name] = self.value
        fields['transport_small_up_sweep_start_freq_dg4162'] = self.dev_up.sweep_start_frequency[self.chinx_up]
        fields['transport_small_up_sweep_stop_freq_dg4162'] = self.dev_up.sweep_stop_frequency[self.chinx_up]
        fields['transport_small_down_sweep_start_freq_dg4162'] = self.dev_down.sweep_start_frequency[self.chinx_down]
        fields['transport_small_down_sweep_stop_freq_dg4162'] = self.dev_down.sweep_stop_frequency[self.chinx_down]
        
        # transport_small_sweep_time_dg4162
        param_name = 'transport_small_sweep_time_dg4162'
        param = self.server.parameters.get(param_name)
        if param is not None:
            value = param.value
            if value is not None:
                fields[param_name] = value
        fields['transport_small_up_sweep_time_dg4162'] = self.dev_up.sweep_time[self.chinx_up]
        fields['transport_small_down_sweep_time_dg4162'] = self.dev_down.sweep_time[self.chinx_down]
        fields['transport_small_up_sweep_return_time_dg4162'] = self.dev_up.sweep_return_time[self.chinx_up]
        fields['transport_small_down_sweep_return_time_dg4162'] = self.dev_down.sweep_return_time[self.chinx_down]
        
        # transport_small_sweep_hold_time_dg4162
        param_name = 'transport_small_sweep_hold_time_dg4162'
        param = self.server.parameters.get(param_name)
        if param is not None:
            value = param.value
            if value is not None:
                fields[param_name] = value
        fields['transport_small_up_sweep_hold_time_dg4162'] = self.dev_up.sweep_hold_time[self.chinx_up]
        fields['transport_small_down_sweep_hold_time_dg4162'] = self.dev_down.sweep_hold_time[self.chinx_down]
        
        write_influxdb_fields(fields)
        
        

Parameter = TransportSmallDG4162SweepAmplitude