"""
### BEGIN NODE INFO
[info]
name = socket
version = 1
description = none
instancename = %LABRADNODE%_socket

[startup]
cmdline = %PYTHON% %FILE%
timeout = 5

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
import json
import socket

from labrad.server import setting

from server_tools.threaded_server import ThreadedServer


class SocketServer(ThreadedServer):
    name = '%LABRADNODE%_socket'
    
    def initServer(self):
        ThreadedServer.initServer(self)
        self._sockets = {}

    def _get_socket(self, _id):
        if _id not in self._sockets:
            self._sockets[_id] = socket.socket()
        return self._sockets[_id]
    
    @setting(10, _id='i', family='i', type='i', proto='i')
    def createsocket(self, c, _id, family, type, proto):
        self._sockets[_id] = socket.socket(family, type, proto)

    @setting(11, _id='i', address='?')
    def connect(self, c, _id, address):
        s = self._get_socket(_id)
        return s.connect(address)

    @setting(12, _id='i')
    def close(self, c, _id):
        s = self._get_socket(_id)
        result = s.close()
        del self._sockets[_id]
        return result

    @setting(13, _id='i')
    def gettimeout(self, c, _id):
        s = self._get_socket(_id)
        return s.gettimeout()
    
    @setting(14, _id='i', buffersize='i', flags='i', returns='s')
    def recv(self, c, _id, buffersize, flags):
        s = self._get_socket(_id)
        return s.recv(buffersize, flags)

    @setting(15, _id='i', data='s', flags='i')
    def send(self, c, _id, data, flags):
        s = self._get_socket(_id)
        return s.send(data, flags)

    @setting(16, _id='i', timeout='v')
    def settimeout(self, c, _id, timeout):
        s = self._get_socket(_id)
        return s.settimeout(timeout)


if __name__ == '__main__':
    from labrad import util
    util.runServer(SocketServer())
