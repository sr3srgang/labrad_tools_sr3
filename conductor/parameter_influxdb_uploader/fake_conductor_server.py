"""
### BEGIN NODE INFO
[info]
name = fake_conductor
version = 1.0
description = Periodic signal emitter for testing subscribers
instancename = fake_conductor

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from labrad.server import LabradServer, Signal
from twisted.internet import reactor
import json
import time

class FakeConductorServer(LabradServer):
    name = "fake_conductor"

    # LabRAD signal: ID 648325, format string ('s' = string)
    update = Signal(648325, 'signal: update', 's')

    def initServer(self):
        self.shot_counter = 0
        self.interval = 5.0  # seconds between signals
        print("[fake_conductor] Server initialized.")
        print(f"[fake_conductor] Starting periodic signal every {self.interval} seconds.")
        self.schedule_next_signal()

    def schedule_next_signal(self):
        reactor.callLater(self.interval, self.emit_signal)

    def emit_signal(self):
        self.shot_counter += 1
        payload = {
            'advance_complete': {
                'experiment': 'fake_conductor_test',
                'shot': self.shot_counter,
                'timestamp': time.time()
            }
        }
        data = json.dumps(payload)
        print(f"[fake_conductor] Emitting signal: {data}", flush=True)
        self.update(data)

        # Schedule next emission
        self.schedule_next_signal()

Server = FakeConductorServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
