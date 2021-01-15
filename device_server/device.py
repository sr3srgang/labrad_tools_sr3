import json
import traceback

from twisted.internet.defer import inlineCallbacks
from labrad import connect

from device_server.exceptions import DeviceInitializationFailed
from device_server.exceptions import DeviceTerminationFailed

class DefaultDevice(object):
    name = None
    servername = None
    server = None

    autostart = False
    update_parameters = []

    def initialize(self, config):
        """ to be implemented by child class """

    def _initialize(self, config):
        """ exception handling of initialize """
        try:
            for key, value in config.items():
                setattr(self, key, value)
            self.initialize(config)
        except:
            raise DeviceInitializationFailed(self.name)
    
    def terminate(self):
        """ to be implemented by child class """

    def _terminate(self):
        """ exception handling of terminate """
        try:
            self.terminate()
        except:
            raise DeviceTerminationFailed(self.name)

    def connect_to_labrad(self):
        connection_name = '{} - {}'.format(self.servername, self.name)
        self.cxn = connect(name=connection_name)

    def get_info(self):
        info = {x: getattr(self, x) for x in dir(self) if x[0] != '_'}
        # ignore item if it cannot be serialized
        info = json.loads(json.dumps(info, default=lambda x: None))
        info = {k: v for k, v in info.items() if v is not None}
        return info


