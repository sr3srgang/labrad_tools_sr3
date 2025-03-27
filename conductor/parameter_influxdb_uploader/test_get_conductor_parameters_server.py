"""
### BEGIN NODE INFO
[info]
name = test_listener_server
version = 1.0
description = Minimal test listener for conductor signals
instancename = test_listener

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from server_tools.threaded_server import ThreadedServer
from twisted.internet.defer import inlineCallbacks
import json
import time


class TestGetConductorParameterServer(ThreadedServer):
    name = "test_get_conductor_parameters_server"

    # @inlineCallbacks
    def initServer(self):
        print(f"[{self.name}] Initializing...")

        conductor_server = self.client.conductor
        request = {}
        # arguments of conductor.get_parameter_values(request_json, all)
        request_json = json.dumps(request, default=lambda x: None)
        all = True
        response_json = conductor_server.get_parameter_values(request_json, all)
        response = json.loads(response_json)
        
        from pprint import pprint, pformat
        msg = pformat(response)
        print(msg)
        # pprint(response)

Server = TestGetConductorParameterServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
