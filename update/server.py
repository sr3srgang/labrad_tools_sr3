"""
### BEGIN NODE INFO
[info]
name = update
version = 1.0
description = 
instancename = update

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.server import setting, LabradServer
from labrad.server import Signal


class UpdateServer(LabradServer):
    name = 'update'
    signal = Signal(1, 'signal: signal', 's')
    updates = {}

    @setting(10, name='s')
    def register(self, c, name):
        if name not in self.updates:
            self.updates[name] = set()
        self.updates[name].add(c.ID)

    @setting(11, name='s')
    def remove(self, c, name):
        if name not in self.updates:
            raise Exception('update does not exist')
        self.updates[name].remove(c.ID)

    @setting(12, name='s', update='s')
    def emit(self, c, name, update):
        if name not in self.updates:
            raise Exception('update does not exist')
        listeners = self.updates[name].copy()
        if c.ID in listeners:
            listeners.remove(c.ID)
        self.signal(update, listeners)

Server = UpdateServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
