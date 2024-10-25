"""
### BEGIN NODE INFO
[info]
name = rf
version = 1.0
description = 
instancename = rf
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
import json
from labrad.server import setting

from device_server.server import DeviceServer

class RFServer(DeviceServer):
    """ Provides basic control for RF sources """
    name = 'rf'
    autostart = True

    @setting(10)
    def states(self, c, request_json='{}'):
        """ get or update device states """
        request = json.loads(request_json)
        response = self._states(request)
        response_json = json.dumps(response)
        return response_json
        
    def _states(self, request):
        if request == {}:
            active_devices = self._get_active_devices()
            request = {device_name: None for device_name in active_devices}
        response = {}
        for device_name, state in request.items():
            device_response = None
            try:
                device_response = self._state(device_name, state)
            except:
                self._reload_device(device_name, {})
                device_response = self._state(device_name, state)
            response.update({device_name: device_response})
        self._send_update({'states': response})
        return response

    def _state(self, name, state):
        device = self._get_device(name)
        if state:
            device.set_state(state)
        response = device.get_state()
        return response
    
    @setting(11)
    def frequencies(self, c, request_json='{}'):
        """ get or update device frequencies """
        request = json.loads(request_json)
        response = self._frequencies(request)
        response_json = json.dumps(response)
        return response_json
        
    def _frequencies(self, request):
        if request == {}:
            active_devices = self._get_active_devices()
            request = {device_name: None for device_name in active_devices}
        response = {}
        for device_name, frequency in request.items():
            device_response = None
            try:
                device_response = self._frequency(device_name, frequency)
            except:
                self._reload_device(device_name, {})
                device_response = self._frequency(device_name, frequency)
            response.update({device_name: device_response})
        self._send_update({'frequencies': response})
        return response

    def _frequency(self, name, frequency):
        device = self._get_device(name)
        if frequency:
            device.set_frequency(frequency)
        response = device.get_frequency()
        return response

    @setting(12)
    def amplitudes(self, c, request_json='{}'):
        """ get or update device amplitudes """
        request = json.loads(request_json)
        response = self._amplitudes(request)
        response_json = json.dumps(response)
        return response_json
        
    def _amplitudes(self, request):
        if request == {}:
            active_devices = self._get_active_devices()
            request = {device_name: None for device_name in active_devices}
        response = {}
        for device_name, amplitude in request.items():
            device_response = None
            try:
                device_response = self._amplitude(device_name, amplitude)
            except:
                self._reload_device(device_name, {})
                device_response = self._amplitude(device_name, amplitude)
            response.update({device_name: device_response})
        self._send_update({'amplitudes': response})
        return response

    def _amplitude(self, name, amplitude):
        device = self._get_device(name)
        if amplitude:
            device.set_amplitude(amplitude)
        response = device.get_amplitude()
        return response
    
    @setting(13)
    def ramprates(self, c, request_json='{}'):
        """ get or update device ramprates """
        request = json.loads(request_json)
        response = self._ramprates(request)
        response_json = json.dumps(response)
        return response_json
        
    def _ramprates(self, request):
        if request == {}:
            active_devices = self._get_active_devices()
            request = {device_name: None for device_name in active_devices}
        response = {}
        for device_name, ramprate in request.items():
            device_response = None
            try:
                device_response = self._ramprate(device_name, ramprate)
            except:
                self._reload_device(device_name, {})
                device_response = self._ramprate(device_name, ramprate)
            response.update({device_name: device_response})
        self._send_update({'ramprates': response})
        return response

    def _ramprate(self, name, ramprate):
        device = self._get_device(name)
        if ramprate:
            device.set_ramprate(ramprate)
        response = device.get_ramprate()
        return response
    
    @setting(14)
    def offsets(self, c, request_json='{}'):
        """ get or update device offsets """
        request = json.loads(request_json)
        response = self._offsets(request)
        response_json = json.dumps(response)
        return response_json
        
    def _offsets(self, request):
        if request == {}:
            active_devices = self._get_active_devices()
            request = {device_name: None for device_name in active_devices}
        response = {}
        for device_name, offset in request.items():
            device_response = None
            try:
                device_response = self._offset(device_name, offset)
            except:
                self._reload_device(device_name, {})
                device_response = self._offset(device_name, offset)
            response.update({device_name: device_response})
        self._send_update({'offsets': response})
        return response

    def _offset(self, name, offset):
        device = self._get_device(name)
        if offset:
            device.set_offset(offset)
        response = device.get_offset()
        return response
    
    @setting(15)
    def linear_ramps(self, c, request_json='{}'):
        """ get or update device linear_ramps """
        request = json.loads(request_json)
        response = self._linear_ramps(request)
        response_json = json.dumps(response)
        print('Called')
        return response_json
        
    def _linear_ramps(self, request):
        if request == {}:
            active_devices = self._get_active_devices()
            request = {device_name: None for device_name in active_devices}
        response = {}
        for device_name, linear_ramp in request.items():
            device_response = None
            try:
                device_response = self._linear_ramp(device_name, linear_ramp)
            except:
                self._reload_device(device_name, {})
                device_response = self._linear_ramp(device_name, linear_ramp)
            response.update({device_name: device_response})
        self._send_update({'linear_ramps': response})
        return response

    def _linear_ramp(self, name, linear_ramp):
        device = self._get_device(name)
        if linear_ramp:
            device.set_linear_ramp(**linear_ramp)
        response = device.get_linear_ramp()
        return response
    
Server = RFServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
