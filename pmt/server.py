"""
### BEGIN NODE INFO
[info]
name = pmt
version = 1.0
description = 
instancename = pmt

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
import json
from labrad.server import setting

from device_server.server import DeviceServer


class PMTServer(DeviceServer):
    name = 'pmt'

    @setting(10)
    def record(self, c, request_json='{}'):
        """ record """
        request = json.loads(request_json)
        response = self._record(request)
        response_json = json.dumps(response)
        return response_json
        
    def _record(self, request):
        response = {}
        for device_name, device_request in request.items():
            device_response = None
            try:
                device_response = self._record_device(device_name, device_request)
            except:
                self._reload_device(device_name, {})
                device_response = self._record_device(device_name, device_request)
            response.update({device_name: device_response})
        self._send_update({'record': response})
        return response

    def _record_device(self, name, request):
        device = self._get_device(name)
        response = None
        if request is not None:
            response = device.record(request)
        return response
    
    @setting(11)
    def retrive_records(self, c, request_json='{}'):
        """ retrive records """
        request = json.loads(request_json)
        response = self._retrive_records(request)
        response_json = json.dumps(response)
        return response_json
        
    def _retrive_records(self, request):
        response = {}
        for device_name, device_request in request.items():
            device_response = None
            try:
                device_response = self._retrive_device_records(device_name, device_request)
            except:
                self._reload_device(device_name, {})
                device_response = self._retrive_device_records(device_name, device_request)
            response.update({device_name: device_response})
        self._send_update({'retrive_records': response})
        return response

    def _retrive_device_records(self, name, request):
        device = self._get_device(name)
        response = device.retrive_records(request)
        return response
    
Server = PMTServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
