import importlib
import json
import numpy as np
import os

from twisted.internet import reactor
from labrad.server import setting
from labrad.server import Signal

from server_tools.threaded_server import ThreadedServer
from device_server.exceptions import DeviceImportFailed
from device_server.exceptions import DeviceNotActive
from device_server.exceptions import DeviceAlreadyActive
from device_server.exceptions import DeviceInitializationFailed
from device_server.exceptions import DeviceTerminationFailed
from device_server.exceptions import DeviceReloadFailed
from device_server.exceptions import DeviceGetInfoFailed

class DeviceServer(ThreadedServer):
    devices = {}
    update = Signal(np.random.randint(0, 2**31 - 1), 'signal: update', 's')
    autostart = False
    
    def initServer(self):
        self.device_directory = os.path.join(os.getenv('PROJECT_LABRAD_TOOLS_PATH'), self.name, 'devices/')
        self._initialize_devices(request={}, all=self.autostart)

    def _import_device(self, device_name):
        try:
            module_path = '{}.devices.{}'.format(self.name, device_name)
            device_class_name = 'Device'
            module = importlib.import_module(module_path)
            reload(module)
            if hasattr(module, device_class_name):
                DeviceClass = getattr(module, device_class_name)
                DeviceClass.name = device_name
                return DeviceClass
            else:
                return None
        except:
            raise DeviceImportFailed(device_name)
    
    def _get_device(self, device_name, initialize=False):
        if device_name not in self.devices:
            if initialize:
                self._initialize_device(device_name, {})
        if device_name not in self.devices:
            raise DeviceNotActive(device_name)
        else:
            return self.devices[device_name]

    @setting(0)
    def get_configured_devices(self, c):
        response = self._get_configured_devices()
        response_json = json.dumps(response, default=lambda x: None)
        return response_json
        
    def _get_configured_devices(self):
        response = {}
        
        device_names = []
        for r, d, f in os.walk(self.device_directory):
            for filename in f:
                full_path = os.path.join(r, filename)
                relative_path = full_path.replace(self.device_directory, '')
                if filename.endswith('__init__.py'):
                    pass
                elif filename.endswith('.py'):
                    dotted_relative_path = relative_path.replace('.py', '').replace('/', '.')
                    device_names.append(dotted_relative_path)
    
        for device_name in device_names:
            DeviceClass = self._import_device(device_name)
            if DeviceClass:
                response.update({device_name: DeviceClass})
        return response

    @setting(1)
    def get_active_devices(self, c):
        response = self._get_active_devices()
        response_json = json.dumps(response, default=lambda x: None)
        return response_json
    
    def _get_active_devices(self):
        return self.devices

    @setting(2, request_json='s', all='b')
    def initialize_devices(self, c, request_json='{}', all=False):
        request = json.loads(request_json)
        response = self._initialize_devices(request, all)
        response_json = json.dumps(response)
        return response_json
    
    def _initialize_devices(self, request={}, all=False):
        if (request == {}) and all:
            configured_devices = self._get_configured_devices()
            request = {
                device_name: {}
                    for device_name, ParameterClass 
                    in configured_devices.items()
                    if ParameterClass.autostart
                }
        response = {}
        for device_name, device_request in request.items():
            device_response = self._initialize_device(device_name, device_request)
            response.update({device_name: device_response})
        return response
    
    def _initialize_device(self, device_name, device_config):
        if device_name in self.devices:
            #raise DeviceAlreadyActive(device_name)
            return
        try:
            DeviceClass = self._import_device(device_name)
            DeviceClass.server = self
            DeviceClass.servername = self.name
            device = DeviceClass()
            device.initialize(device_config)
            self.devices[device_name] = device
        except DeviceInitializationFailed:
            raise
        except:
            raise DeviceInitializationFailed(device_name)

    @setting(3, request_json='s', all='b')
    def terminate_devices(self, c, request_json='{}', all=False):
        request = json.loads(request_json)
        response = self._terminate_devices(request, all)
        response_json = json.dumps(response)
        return response_json
    
    def _terminate_devices(self, request={}, all=False):
        if (request == {}) and all:
            active_devices = self._get_active_devices()
            request = {
                device_name: {}
                    for device_name, ParameterClass 
                    in active_devices.items()
                }
        response = {}
        for device_name, device_request in request.items():
            device_response = self._terminate_device(device_name, device_request)
            response.update({device_name: device_response})
        return response
   
    def _terminate_device(self, device_name, device_config):
        try:
            device = self._get_device(device_name)
            device._terminate()
            del self.devices[device_name]
        except DeviceNotActive:
            raise
        except DeviceTerminationFailed:
            del self.devices[device_name]
            raise
        except:
            del self.devices[device_name]
            raise DeviceTerminationFailed(device_name)
    
    @setting(4, request_json='s', all='b')
    def reload_devices(self, c, request_json='{}', all=False):
        request = json.loads(request_json)
        response = self._reload_devices(request, all)
        response_json = json.dumps(response)
        return response_json
    
    def _reload_devices(self, request={}, all=False):
        if (request == {}) and all:
            active_devices = self._get_active_devices()
            request = {
                device_name: {}
                    for device_name, ParameterClass 
                    in active_devices.items()
                }
        response = {}
        for device_name, device_config in request.items():
            device_response = self._reload_device(device_name, device_config)
            response.update({device_name: device_response})
        return response
    
    def _reload_device(self, device_name, device_config):
        try:
            try:
                self._terminate_device(device_name, device_config)
            except DeviceNotActive:
                pass
            self._initialize_device(device_name, device_config)
        except:
            raise DeviceReloadFailed(device_name)

    @setting(5, request_json='s', all='b')
    def get_device_infos(self, c, request_json='{}', all=True):
        request = json.loads(request_json)
        response = self._get_device_infos(request, all)
        response_json = json.dumps(response)
        return response_json
    
    def _get_device_infos(self, request={}, all=True):
        if (request == {}) and all:
            active_devices = self._get_active_devices()
            request = {
                device_name: {}
                    for device_name, ParameterClass 
                    in active_devices.items()
                }
        response = {}
        for device_name in request:
            device_response = self._get_device_info(device_name)
            response.update({device_name: device_response})
        return response

    def _get_device_info(self, device_name):
        try:
            device = self._get_device(device_name)
            device_info = device.get_info()
        except:
            raise DeviceGetInfoFailed(device_name)
        return device_info
    
    def _send_update(self, update={}):
        update_json = json.dumps(update)
        self.update(update_json)

    @setting(6, request_json='s', returns='s')
    def call(self, c, request_json):
        request = json.loads(request_json)
        response = {}
        for device_name, device_request in request.items():
            device = self._get_device(device_name, True)
            device_response = {}
            for method_name, method_request in device_request.items():
                method = getattr(device, method_name)
                args = method_request.get('args', [])
                kwargs = method_request.get('kwargs', {})
                method_response = method(*args, **kwargs)
                device_response[method_name] = method_response
            response[device_name] = device_response
        return json.dumps(response)
    
    @setting(7, request_json='s')
    def call_in_thread(self, c, request_json):
        request = json.loads(request_json)
        response = {}
        for device_name, device_request in request.items():
            device = self._get_device(device_name, True)
            device_response = {}
            for method_name, method_request in device_request.items():
                method = getattr(device, method_name)
                args = method_request.get('args', [])
                kwargs = method_request.get('kwargs', {})
                reactor.callInThread(method, *args, **kwargs)
    
    @setting(8, request_json='s', returns='s')
    def set(self, c, request_json):
        request = json.loads(request_json)
        response = {}
        for device_name, device_request in request.items():
            device = self._get_device(device_name, True)
            device_response = {}
            for attribute_name, attribute_request in device_request.items():
                setattr(device, attribute_name, attribute_request)
                device_response[attribute_name] = attribute_request
            response[device_name] = device_response
        return json.dumps(response)
    
    @setting(9, request_json='s', returns='s')
    def get(self, c, request_json):
        request = json.loads(request_json)
        response = {}
        for device_name, device_request in request.items():
            device = self._get_device(device_name, True)
            device_response = {}
            for attribute_name, attribute_request in device_request.items():
                attribute = getattr(device, attribute_name)
                device_response[attribute_name] = attribute
            response[device_name] = device_response
        return json.dumps(response)





