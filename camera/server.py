
import json
from labrad.server import setting

from device_server.server import DeviceServer


class CameraServer(DeviceServer):
    name = 'camera'

    @setting(10)
    def record(self, c, cam, paths):
        """ Sends message out to camera clients to tell them to record"""
        self._send_update({cam: paths})
        print(paths)
    
Server = CameraServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
