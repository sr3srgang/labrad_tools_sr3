
import json
from labrad.server import setting, LabradServer

from device_server.server import DeviceServer
from twisted.internet import defer, reactor

class PicoServer(DeviceServer):
    name = 'pico'
    
    def initServer(self):
    	#self.
    	self._lock = defer.DeferredLock()
    	print('hello')

    @setting(10)
    def record(self, c, request_json='{}'):
        """ record """
        print('called')
        request = json.loads(request_json)
        print('starting record')
        #self._record(request)
        #self._lock.run(self._record, request)
        #response_json = json.dumps(response)
     	
        #return response_json
        reactor.callInThread(self.record_in_thread, request)
        
    def record_in_thread(self, request):
    	self._lock.run(self._record, request)
        
    def _record(self, request):
        response = {}
        for device_name, device_request in request.items():
            device_response = None
            try:
            	device_response = self._record_device(device_name, device_request)
            	print('_record_device finished')
            except:
                print('Error!!')
                self._reload_device(device_name, {})
                device_response = self._record_device(device_name, device_request)
            
#            response.update({device_name: device_response})
 #       self._send_update({'record': response})
        #return response

    def _record_device(self, name, request):
        device = self._get_device(name)
        print('_record_device executing')
        response = None
        if request is not None:
        	response = self._lock.run(device.record, request)
        	#device.record(request)
        return response

Server = PicoServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
