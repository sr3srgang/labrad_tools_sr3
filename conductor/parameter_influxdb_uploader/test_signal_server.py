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
import json
import time

class TestSignalSubscriptionServer(ThreadedServer):
    name = "test_signal_subscription_server"

    # print useful debug messages if enabled
    DEBUG_MODE = True
    def print_debug(self, msg):
        if self.DEBUG_MODE is not True:
            return
        print("[DEBUG] " + str(msg) + "\n\tfrom " + __file__, flush=True)

    def initServer(self):
        print(f"[{self.name}] Initializing...")

        # Subscribe to conductor.update signal (ID 648324)
        # self.client.conductor.signal__update(648324)  # tell manager to send us this signal
        # signal_id = (self.client.conductor.ID, 648325)  # signal ID tuple
        self.client.fake_conductor.signal__update(648325)  # tell manager to send us this signal
        signal_id = (self.client.fake_conductor.ID, 648325)  # signal ID tuple
        self.print_debug(f"signal_id = {signal_id}")
        self._cxn.addListener(signal_id, self.on_conductor_update)

        print(f"[{self.name}] Subscribed to conductor.update signal")

    def on_conductor_update(self, c, data):
        """ Callback for when conductor sends a signal """
        print(f"[{self.name}] Received signal:", flush=True)
        try:
            update = json.loads(data)
        except Exception as e:
            print(f"[{self.name}] Failed to decode JSON:", e)
            return

        print(f"[{self.name}] Received signal:", update, flush=True)

        if 'advance_complete' in update:
            payload = update['advance_complete']
            print(f"[{self.name}] --> Shot {payload.get('shot')} from experiment '{payload.get('experiment')}'")
            self.call_in_thread(self.handle_advance_complete, payload)

    def handle_advance_complete(self, payload):
        """ Runs in background thread to simulate work """
        time.sleep(2)
        print(f"[{self.name}] Done processing shot {payload.get('shot')}", flush=True)

Server = TestSignalSubscriptionServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
