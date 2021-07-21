
import json, time
from labrad.server import setting

from device_server.server import DeviceServer


class CameraServer(DeviceServer):
    name = 'camera'

    @setting(10)
    def record(self, c, cam, paths):
        """ Sends message out to camera clients to tell them to record"""
        self._send_update({cam: paths})
        #print(paths)
        
    @setting(11)
    def reset(self, c, cam):
    	print("RESET CALLED")
    	self._send_update({'reset': None})
    
Server = CameraServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
