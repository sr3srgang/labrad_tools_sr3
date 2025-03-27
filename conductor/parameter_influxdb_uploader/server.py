from server_tools.threaded_server import ThreadedServer
from twisted.internet.defer import inlineCallbacks
import json
import time

class ConductorParameterInfluxDBUploader(ThreadedServer):
    name = "conductor_parameter_influxdb_uploader_server"

    @inlineCallbacks
    def initServer(self):
        yield self.client.conductor.signal__update(648324)
        signal_id = (self.client.conductor.ID, 648324)
        self.client._cxn.addListener(signal_id, self.on_conductor_update)
        print("[uploader] Subscribed to conductor.update signal")

    def on_conductor_update(self, c, data):
        try:
            update = json.loads(data)
        except Exception as e:
            print("[uploader] Failed to parse signal:", e)
            return

        if 'advance_complete' in update:
            self.call_in_thread(self.handle_advance_complete, update['advance_complete'])

    def handle_advance_complete(self, payload):
        print(f"[uploader] Got shot {payload['shot']} from experiment {payload['experiment']}")
        time.sleep(2)  # Simulate upload delay
        print("[uploader] Done processing")

Server = ConductorParameterInfluxDBUploader

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
