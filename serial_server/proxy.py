class SerialProxy(object):
    def __init__(self, serial_server):
        self.serial_server = serial_server

    def Serial(self, comport):
        ser = Serial(self.serial_server, comport)
        return ser

class Serial(object):
    def __init__(self, serial_server, comport):
        self.serial_server = serial_server
        self.comport = comport
        print(comport)
        self.serial_server.reopen_interface(self.comport)

    @property
    def baudrate(self):
        return self.serial_server.baudrate(self.comport)
    
    @baudrate.setter
    def baudrate(self, baudrate):
        self.serial_server.baudrate(self.comport, baudrate)

    @property
    def bytesize(self):
        return self.serial_server.bytesize(self.comport)
    
    @bytesize.setter
    def bytesize(self, bytesize):
        self.serial_server.bytesize(self.comport, bytesize)
    
    @property
    def dsrdtr(self):
        return self.serial_server.dsrdtr(self.comport)
    
    @dsrdtr.setter
    def dsrdtr(self, dsrdtr):
        self.serial_server.dsrdtr(self.comport, dsrdtr)
    
    @property
    def parity(self):
        return self.serial_server.parity(self.comport)
    
    @parity.setter
    def parity(self, parity):
        self.serial_server.parity(self.comport, parity)
    
    def read(self, size=1):
        return self.serial_server.read(self.comport, size)
    
    def read_until(self, expected='\n', size=1):
        return self.serial_server.read_until(self.comport, expected, size)
    
    def readline(self, size=-1):
        return self.serial_server.readline(self.comport, size)
    
    def readlines(self, size=-1):
        return self.serial_server.readlines(self.comport, size)
    
    @property
    def rtscts(self):
        return self.serial_server.rtscts(self.comport)
    
    @rtscts.setter
    def rtscts(self, rtscts):
        self.serial_server.rtscts(self.comport, rtscts)
    
    @property
    def stopbits(self):
        return self.serial_server.stopbits(self.comport)
    
    @stopbits.setter
    def stopbits(self, stopbits):
        self.serial_server.stopbits(self.comport, stopbits)
    
    @property
    def timeout(self):
        return self.serial_server.timeout(self.comport)
    
    @timeout.setter
    def timeout(self, timeout):
        self.serial_server.timeout(self.comport, timeout)
    
    def write(self, data):
        return self.serial_server.write(self.comport, data)
    
    def writelines(self, data):
        return self.serial_server.writelines(self.comport, data)
    
