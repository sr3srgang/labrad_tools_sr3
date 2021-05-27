import json
from labrad.server import setting, LabradServer

from device_server.server import DeviceServer
from twisted.internet import defer, reactor

class PicoServer(DeviceServer):
	name = 'pico'
	
	@setting(10)
	def record(self, c, request_json = '{}'):
		request = json.loads(request_json)
		for device_name, device_request in request.items():
			device = self._get_device(device_name)
			device.record(device_request)
	@setting(11)
	def set_max_V(self, c, request_json = '{}'):
		request = json.loads(request_json)
		for device_name, device_request in request.items():
			device = self._get_device(device_name)
			device.set_max_V(device_request)
			
			
Server = PicoServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
