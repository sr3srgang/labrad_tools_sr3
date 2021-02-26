import json
import numpy as np
import socket


class SocketProxy(object):
    AF_INET = socket.AF_INET
    SOCK_STREAM = socket.SOCK_STREAM

    def __init__(self, server):
        self._server = server

    def socket(self, family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
        return Socket(self._server, family, type, proto)


class Socket(object):
    """
    socket([family[, type[, proto]]]) -> socket object

    Open a socket of the given type.  The family argument specifies the
    address family; it defaults to AF_INET.  The type argument specifies
    whether this is a stream (SOCK_STREAM, this is the default)
    or datagram (SOCK_DGRAM) socket.  The protocol argument defaults to 0,
    specifying the default protocol.  Keyword arguments are accepted.

    A socket object represents one endpoint of a network connection.

    Methods of socket objects (keyword arguments not allowed):

    close() -- close the socket
    connect(addr) -- connect the socket to a remote address
    dup() -- return a new socket object identical to the current one [*][**]
    fileno() -- return underlying file descriptor [**]
    getpeername() -- return remote address [*][**]
    getsockname() -- return local address [**]
    getsockopt(level, optname[, buflen]) -- get socket options [**]
    gettimeout() -- return timeout or None
    listen(n) -- start listening for incoming connections [**]
    makefile([mode, [bufsize]]) -- return a file object for the socket [*][**]
    recv(buflen[, flags]) -- receive data
    recv_into(buffer[, nbytes[, flags]]) -- receive data (into a buffer) [**]
    recvfrom(buflen[, flags]) -- receive data and sender's address [**]
    recvfrom_into(buffer[, nbytes, [, flags]) [**]
    -- receive data and sender's address (into a buffer)
    sendall(data[, flags]) -- send all data [**]
    send(data[, flags]) -- send data, may not send all of it
    sendto(data[, flags], addr) -- send data to a given address [**]
    setblocking(0 | 1) -- set or clear the blocking I/O flag [**]
    setsockopt(level, optname, value) -- set socket options [**]
    settimeout(None | float) -- set or clear the timeout
    shutdown(how) -- shut down traffic in one or both directions [**]

    [*] not available on all platforms!
    [**] not implemented in labrad proxy
    """

    def __init__(self, server, family=socket.AF_INET, type=socket.SOCK_STREAM, 
                 proto=0):
        self._server = server
        self.family = family
        self.type = type
        self.proto = proto

        self._id = np.random.randint(0, 2**31 - 1)
    
    def close(self):
        """
        close()
        
        Close the socket.  It cannot be used after this call.
        """
        return self._server.close(self._id)

    def connect(self, address):
        """ 
        connect(address)

        Connect the socket to a remote address.  For IP sockets, the address
        is a pair (host, port).
        """
        return self._server.connect(self._id, address)

    def gettimeout(self):
        """
        gettimeout() -> timeout

        Returns the timeout in seconds (float) associated with socket 
        operations. A timeout of None indicates that timeouts on socket 
        operations are disabled.
        """
        return self._server.gettimeout(self._id)

    def recv(self, buffersize, flags=0):
        """
        recv(buffersize[, flags]) -> data
        
        Receive up to buffersize bytes from the socket.  For the optional flags
        argument, see the Unix manual.  When no data is available, block until
        at least one byte is available or until the remote end is closed.  When
        the remote end is closed and all data is read, return the empty string.

        """
        return self._server.recv(self._id, buffersize, flags)

    def send(self, data, flags=0):
        """
        send(data[, flags]) -> count

        Send a data string to the socket.  For the optional flags
        argument, see the Unix manual.  Return the number of bytes
        sent; this may be less than len(data) if the network is busy.
        """
        return self._server.send(self._id, data, flags)

    def settimeout(self, timeout):
        """
        settimeout(timeout)

        Set a timeout on socket operations.  'timeout' can be a float,
        giving in seconds, or None.  Setting a timeout of None disables
        the timeout feature and is equivalent to setblocking(1).
        Setting a timeout of zero is the same as setblocking(0).
        """
        return self._server.settimeout(self._id, timeout)

SocketProxy.socket.__func__.__doc__ = Socket.__doc__
