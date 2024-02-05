import json
from labrad.server import setting, LabradServer

from device_server.server import DeviceServer
from twisted.internet import defer, reactor
import time

class PicoServer(DeviceServer):
	name = 'cavity_probe_pico'
	
	@setting(10)
	def record(self, c, request_json = '{}'):
		start = time.time()
		print('Cavity probe pico server called')
		request = json.loads(request_json)
		for device_name, device_request in request.items():
			device = self._get_device(device_name)
			device.record(device_request)
		end = time.time()
		print('time elapsed for server: {}'.format(end - start))
	
	@setting(13)
	def send_sweep_params(self, c, request_json = '{}'):
		request = json.loads(request_json)
		message = {'params': request}
		self._send_update(message)
		print(request_json)		
		
	@setting(12)
	def set_max_V(self, c, request_json = '{}'):
		request = json.loads(request_json)
		for device_name, device_request in request.items():
			device = self._get_device(device_name)
			device.set_max_V(device_request)
		
	@setting(11)
	def reset(self, c):
		device = self._get_device('cavity_probe_pico')
		device.reset()
		print('Pico armed')	
			
Server = PicoServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())

    #Server.initialize_devices(json.dumps({'cavity_pico': {}}))
    #print('test')
