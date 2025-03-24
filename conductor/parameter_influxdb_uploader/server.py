from server_tools.threaded_server import ThreadedServer  # Instead of LabradServer

class ConductorParameterInfluxDBUploader(ThreadedServer):  # Just inherit from ThreadedServer
    name = "conductor_parameter_influxdb_uploader_server"
    
    @inlineCallbacks
    def initServer(self):
        yield self.client.conductor.signal__update(648324)
        yield self.client.conductor.addListener(listener=self.on_conductor_update, ID=648324)

    def on_conductor_update(self, c, data):
        update = json.loads(data)
        if 'advance_complete' in update:
            # Safely handle slow stuff in a thread
            self.call_in_thread(self.handle_advance_complete, update['advance_complete'])

    def handle_advance_complete(self, payload):
        # Safe to block here
        print(f"Got shot {payload['shot']} from experiment {payload['experiment']}")
        time.sleep(2)  # Simulate delay
        print("Done processing")
        
        
Server = ConductorParameterInfluxDBUploader

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
