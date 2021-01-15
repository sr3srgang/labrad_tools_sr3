"""
### BEGIN NODE INFO
[info]
name = sequencer
version = 1.0
description = 
instancename = sequencer

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
import json
import time

from twisted.internet import reactor
from labrad.server import Signal
from labrad.server import setting

from device_server.server import DeviceServer

from sequencer.exceptions import ChannelNotFound

UPDATE_ID = 698032

def master_last(devices):
    return sorted([device_name for device_name in devices], 
                  key=lambda x: devices[x].is_master)

class SequencerServer(DeviceServer):
    name = 'sequencer'
    update = Signal(UPDATE_ID, 'signal: update', 's')
    
    def _get_channel(self, channel_id):
        """
        expect 3 possibilities for channel_id.
        1) name -> return channel with that name
        2) @loc -> return channel at that location
        3) name@loc -> first try name, then location
        """
        channel = None
        for device in self.devices.values():
            response = device.get_channel(channel_id, suppress_error=True)
            if response is not None:
                channel = response
                break
        if channel is None:
            raise ChannelNotFound(channel_id)
        return channel
    
    @setting(10)
    def get_channel_infos(self, c, request_json='{}'):
        request = json.loads(request_json)
        response = self._get_channel_infos(request)
        response_json = json.dumps(response)
        return response_json
    
    def _get_channel_infos(self, request={}):
        if request == {}:
            request = {
                device_name: {
                    channel.key: None
                        for channel in device.channels
                    } 
                    for device_name, device in self.devices.items()
                }
        response = {}
        for device_name, device_request in request.items():
            device_response = {}
            device = self._get_device(device_name)
            for channel_name, channel_request in device_request.items():
                channel = self._get_channel(channel_name)
                channel_response = channel.get_info()
                device_response.update({channel_name: channel_response})
            response.update({device_name: device_response})
        self._send_update({'channel_infos': response})
        return response
    
    @setting(11)
    def channel_modes(self, c, request_json='{}'):
        request = json.loads(request_json)
        response = self._channel_modes(request)
        response_json = json.dumps(response)
        return response_json
    
    def _channel_modes(self, request={}):
        if request == {}:
            request = {
                device_name: {
                    channel.key: None
                        for channel in device.channels
                    } 
                    for device_name, device in self.devices.items()
                }
        response = {}
        for device_name, device_request in request.items():
            device_response = {}
            device = self._get_device(device_name)
            for channel_name, channel_mode in device_request.items():
                channel = self._get_channel(channel_name)
                if channel_mode is not None:
                    channel.set_mode(channel_mode)
                channel_response = channel.get_mode()
                device_response.update({channel_name: channel_response})
            device.update_channel_modes()
            response.update({device_name: device_response})
        self._send_update({'channel_modes': response})
        return response
    
    @setting(12)
    def channel_manual_outputs(self, c, request_json='{}'):
        request = json.loads(request_json)
        response = self._channel_manual_outputs(request)
        response_json = json.dumps(response)
        return response_json
    
    def _channel_manual_outputs(self, request):
        if request == {}:
            request = {
                device_name: {
                    channel.key: None
                        for channel in device.channels
                    } 
                    for device_name, device in self.devices.items()
                }
        response = {}
        for device_name, device_request in request.items():
            device_response = {}
            device = self._get_device(device_name)
            for channel_name, channel_manual_output in device_request.items():
                channel = self._get_channel(channel_name)
                if channel_manual_output is not None:
                    channel.set_manual_output(channel_manual_output)
                channel_response = channel.get_manual_output()
                device_response.update({channel_name: channel_response})
            device.update_channel_manual_outputs()
            response.update({device_name: device_response})
        self._send_update({'channel_manual_outputs': response})
        return response

    @setting(13, request_json='s', tmpdir='b')
    def fix_sequence_keys(self, c, request_json='{}', tmpdir=True):
        """ client sends list of strings, device by device, we go into sequence folder, read, fix, write

        slave devices go after master device so they can fill in missing channel sequences (default to manual outs)
        each device thus needs its own fix_sequence_keys method
        
        """
        request = json.loads(request_json)
        response = self._fix_sequence_keys(request, tmpdir)
        response_json = json.dumps(response)
        return response_json
    
    def _fix_sequence_keys(self, request={}, tmpdir=True):
        response = {}
        for device_name, device_request in request.items():
            device = self._get_device(device_name)
            device_response = device.fix_sequence_keys(device_request, tmpdir)
            response.update({device_name: device_response})
        return response
    
    @setting(14)
    def sequence(self, c, request_json='{}'):
        """ sequence at this point must be list of strings """
        request = json.loads(request_json)
        response = self._sequence(request)
        response_json = json.dumps(response)
        return response_json

    def _sequence(self, request={}):
        if request == {}:
            request = {device_name: None for device_name in self.devices}
        response = {}
        for device_name, device_request in request.items():
            device = self._get_device(device_name)
            if device_request is not None:
                device.set_sequence(device_request)
            device_response = device.get_sequence()
            response.update({device_name: device_response})
        self._send_update({'sequence': response})
        return response

#   @setting(114)
#    def set_sequence_fast(self, c, request_json='{}'):
#        request = json.loads(request_json)
#        response = self._set_sequence_fast(request)
#    
#    def _set_sequence_fast(self, request={}):
#        for device_name, device_request in request.items():
#            reactor.callInThread(self._set_device_sequence_fast, device_name, 
#                                 device_request)
#
#    def _set_device_sequence_fast(self, name, request=None):
#        device = self._get_device(name)
#        if request is not None:
#            device.set_sequence(request)
#
    @setting(15)
    def running(self, c, request_json='{}'):
        request = json.loads(request_json)
        response = self._running(request)
        response_json = json.dumps(response)
        return response_json
    
    def _running(self, request={}):
        if request == {}:
            request = {device_name: None for device_name in self.devices}
        for device_name in master_last(self.devices):
            device = self._get_device(device_name)
            device_request = request.get(device_name)
            if device_request is not None:
                device.set_running(device_request)
        response = {}
        for device_name in request:
            device = self._get_device(device_name)
            device_response = device.get_running()
            response.update({device_name: device_response})
        self._send_update({'running': response})
        return response
    
Server = SequencerServer()
    
if __name__ == "__main__":
    from labrad import util
    reactor.suggestThreadPoolSize(4)
    util.runServer(Server)
