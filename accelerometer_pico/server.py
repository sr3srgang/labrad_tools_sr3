import json
from labrad.server import setting, LabradServer

from device_server.server import DeviceServer
from twisted.internet import defer, reactor
import time

class PicoServer(DeviceServer):
	name = 'accelerometer_pico'
	
	@setting(10)
	def record(self, c, request_json = '{}'):
		start = time.time()
		print('Accelerometer pico server called')
		request = json.loads(request_json)
		for device_name, device_request in request.items():
			device = self._get_device(device_name)
			device.record(device_request)
		end = time.time()
		print(end - start)
			
			
	@setting(12)
	def set_max_V(self, c, request_json = '{}'):
		request = json.loads(request_json)
		for device_name, device_request in request.items():
			device = self._get_device(device_name)
			device.set_max_V(device_request)
		
	@setting(11)
	def reset(self, c):
		device = self._get_device('accelerometer_pico')
		device.reset()
		print('Pico armed')	
			
Server = PicoServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())

    #Server.initialize_devices(json.dumps({'cavity_pico': {}}))
    #print('test')
