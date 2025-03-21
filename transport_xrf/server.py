from labrad.server import setting #, LabradServer
from device_server.server import DeviceServer
import json
# from twisted.internet import defer, reactor

import jsonplus
import time

class TransportXRFServer(DeviceServer):
    # name as a Labrad server
    # Also, name in the DeviceServer.devices static dictionary (via DeviceServer._initialize_devices())
	name = 'transport_xrf_device_server'
	
	# print useful debug messages if enabled
	DEBUG_MODE = True
	def print_debug(self, str):
		if self.DEBUG_MODE is not True:
			return
		print("[DEBUG] " + str + "\n\tfrom " + __file__)

	# essentially inherited LabradServers's __init__ method; no need to modify it.
	# In particular, the object already has Labrad client `self.cxn` defined.
 
	# Caution: setting number has to start from 10. 0 -- 9 are reserved for DeviceServer. 	
 
	@setting(10)
	def update(self, c, request_jsonplus = '{}'): # use jsonplus instead of json to preserve tuple type in transport sequence
		start = time.time()		
		self.print_debug('transport_xrf_device_server.update() called.')		
		request = jsonplus.loads(request_jsonplus) # got transport_sequence from `transport_xrf.small_table_script_generator`` conductor parameter.		re
		transport_sequence = request['transport_sequence']
		self.print_debug('Got transport sequence: {}'.format(transport_sequence))

		end = time.time()
		print(f"Time elapsed for arming transport_xrf = {end - start} s.")
		
	
Server = TransportXRFServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())

    #Server.initialize_devices(json.dumps({'cavity_pico': {}}))
    #print('test')