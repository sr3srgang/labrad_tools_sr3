import json
import os
import pkgutil

from twisted.internet.defer import inlineCallbacks
from twisted.internet.defer import returnValue
from labrad.server import LabradServer
from labrad.server import setting
from labrad.wrappers import connectAsync

from exceptions import DeviceAlreadyInitializedError
from exceptions import DeviceImportError
from exceptions import DeviceInitializationError
from exceptions import DeviceTerminationError
from helpers import import_device_class

class GenericDevice(object):
    autostart = False
    parameters = {}

    def __init__(self, config):
        for key, value in config.items():
            setattr(self, key, value)
    
    @inlineCallbacks
    def connect_labrad(self):
        connection_name = '{} - {}'.format(self.device_server_name, self.name)
        self.cxn = yield connectAsync(name=connection_name)
    
    def initialize(self):
        pass

    def terminate(self):
        pass

    def set(self, settings):
        pass

    def get(self, settings):
        pass


class DeviceServer(LabradServer):
    devices = {}
    
    @inlineCallbacks
    def initServer(self):
        configured_devices = self._get_configured_devices()
        autostart_devices = {device_name: {}
                for device_name, DeviceClass in configured_devices.items()
                if DeviceClass.autostart}
        yield self._initialize_devices(autostart_devices)
    
    def _get_configured_devices(self):
        configured_devices_directory = './devices/'
        configured_devices = {}
        if os.path.isdir(configured_devices_directory):
            device_names = [name for _, name, ispkg in 
                pkgutil.iter_modules([configured_devices_directory])
                if not ispkg
                ]
            for device_name in device_names:
                DeviceClass = import_device(device_name)
                if DeviceClass:
                    configured_devices.update({device_name: DeviceClass})
        return configured_devices
    
    @inlineCallbacks
    def _initialize_devices(self, devices_config):
        for device_name, device_config in devices_config.items():
            yield self._initialize_device(device_name, device_config)
    
    @inlineCallbacks 
    def _initialize_device(self, device_name, device_config={}):
        if device_name in self.devices:
            raise DeviceAlreadyRegistered(device_name)
        try:
            DeviceClass = import_device(device_name)
            DeviceClass.device_server = self
            DeviceClass.device_server_name = self.name
            device = DeviceClass(device_config)
            yield device.initialize()
            self.devices[device_name] = device
        except:
            raise DeviceInitializationFailed(device_name)

    @inlineCallbacks 
    def _terminate_device(self, device_name):
        if device_name not in self.devices:
            raise DeviceNotRegistered(device_name)
        try:
            device = self.devices.pop(device_name)
            yield device.terminate(device_config)
        except:
            raise DeviceTerminationFailed(device_name)
        finally:
            del device

    def get_selected_device(self, c):
        device_name = c.get('device_name')
        if device_name is None:
            raise NoSelectedDevice()
        return self.devices[device_name]
    
    @setting(0, returns='s')
    def list_devices(self, c):
        """ list available devices
        
        Args:
            None
        Returns:
            json dumped dict
            {
                'active': active_devices,
                'configured': configured_devices,
            }
            where active_devices is list of names of running devices
            and configured_devices is list of names of devices configured in './devices'
        """
        active_device_names = self.devices.keys()
        configured_device_names = self._get_configured_devices().keys()
        response = {
            'active': active_device_names,
            'configured': configured_device_names,
            }
        return json.dumps(response)

    @setting(1, device_name='s', returns=['s', ''])
    def select_device(self, c, device_name):
        if device_name not in self.devices.keys():
            yield self._initialize_device(device_name)

        c['device_name'] = device_name
        device = self.get_selected_device(c)
        device_info = {x: getattr(device, x) for x in dir(device) if x[0] != '_'}
        
        # ignore if cannot serialise
        device_info = json.loads(json.dumps(device_info, default=lambda x: None))
        device_info = {k: v for k, v in device_info.items() if v is not None}
        returnValue(json.dumps(device_info))
    
    @setting(2, device_config_json='s', returns='s')
    def initialize_device(self, c, device_config_json='{}'):
        device_config = json.loads(device_config_json)
        device = self.get_selected_device(c)
        device_name = device.name
        yield self._initialize_device(device_name, device_config)
        device_info_json = yield self.select_device(c, device_name)
        returnValue(device_info_json)
    
    @setting(3)
    def terminate_device(self, c):
        device = self.get_selected_device(c)
        device_name = device.name
        yield self._terminate_device(device_name)
    
    @setting(4)
    def reload_device(self, c):
        device = self.get_selected_device(c)
        device_name = device.name
        if device_name in self.devices:
            yield self._terminate_device(device_name)
        yield self._initialize_device(device_name)
    
    @setting(5)
    def send_update(self, c):
        device = self.get_selected_device(c)
        update = {c['device_name']: {p: getattr(device, p) 
                  for p in device.update_parameters}}
        yield self.update(json.dumps(update))


