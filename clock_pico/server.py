import json
from labrad.server import setting, LabradServer

from device_server.server import DeviceServer
from twisted.internet import defer, reactor
import time

class PicoServer(DeviceServer):
	name = 'clock_pico'
	
	@setting(10)
	def record(self, c, request_json = '{}'):
		start = time.time()
		print('Pico server called')
		request = json.loads(request_json)
		for device_name, device_request in request.items():
			device = self._get_device(device_name)
			device.record(device_request)
		end = time.time()
		print("Time elapsed for server: " + str(end - start))
	
	@setting(11)
	def reset(self, c):
		device = self._get_device('clock_pico')
		device.reset()
		print('Pico armed')		
	'''		
	@setting(11)
	def set_max_V(self, c, request_json = '{}'):
		request = json.loads(request_json)
		for device_name, device_request in request.items():
			device = self._get_device(device_name)
			device.set_max_V(device_request)
	'''		
			
Server = PicoServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())

    #Server.initialize_devices(json.dumps({'cavity_pico': {}}))
    #print('test')
