## low-level codes for communication with & control Time-Base DIM-3000 AOM driver

class DeviceCommunicationError(Exception):
    pass

class FrequencyOutOfBoundsError(Exception):
    pass

class AmplitudeOutOfBoundsError(Exception):
    pass

# each sent/received strings end with a linebreak (CR+LF)
ENDSTR =  b"\r\n" 

class DIM3000(object):
    _frequency_range = (10e6, 400e6)
    _telnetlib_host = None # IP address of the EUR-1D Ethernet-USB Router
    _telnetlib_port  = None # port set to EUR-1D (default: 8081)
    _custom_name = None # Custom-Name of the DIM-3000 device to control
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if 'telnetlib' not in globals():
            global telnetlib
            import telnetlib
        if 'np' not in globals():
            global np
            import numpy as np

    def _init_connection(self):
        try:
            # create telnet object & open connection
            tn = telnetlib.Telnet(self._telnetlib_host, self._telnetlib_port)
            # read away ininitial message "CONNECT"
            # print("DIM3000 connection successful.")
            msg = tn.read_until(ENDSTR, timeout=0.5)
            # print("DIM3000: message received: "); print(msg)
            ans = msg.rstrip(ENDSTR).decode()
            # print("DIM3000: message received: "); print(msg)
            if ans != "CONNECTED":
                print("Wrong DIM3000 connection message recieved: " + ans)
                raise DeviceCommunicationError()
            
            # return opened telnet object
            return tn
        except Exception as ex:
            raise DeviceCommunicationError()
    
    @property
    def frequency(self):
        # open telnet connection
        tn =  self._init_connection()
        # send command
        command = "{}|FRQ?".format(self._custom_name)
        msg = command.encode() + ENDSTR
        # receive response
        msg = tn.read_until(ENDSTR, timeout=0.5)
        ans = msg.rstrip(ENDSTR).decode()
        # close connection
        tn.close()
        
        return float(ans)
    
    @frequency.setter
    def frequency(self, frequency):
        # check input frequency
        if frequency % 1 != 0: # not integer
            print("WARNING: DIM3000 frequency can be set to integer Hz! Your input %f Hz is rounded to %.0f Hz" % (frequency, frequency))
            frequency = np.round(frequency)
        
        # open telnet connection
        tn =  self._init_connection()
        if frequency < min(self._frequency_range) or frequency > max(self._frequency_range):
            raise FrequencyOutOfBoundsError(frequency)
        # send commandd
        command = self._custom_name + "|FRQ:%.0f" %  frequency
        msg = command.encode() + ENDSTR
        # print("DIM3000: message to sent: "); print(msg)
        tn.write(msg)
        # close connection
        tn.close()

        
# class DIM3000Proxy(DIM3000):
#     _telnetlib_servername = None

#     def __init__(self, cxn=None, **kwargs):
#         if cxn == None:
#             import labrad
#             cxn = labrad.connect()
#         from vxi11_server.proxy import Vxi11Proxy
#         global vxi11
#         vxi11 = Vxi11Proxy(cxn[self._vxi11_servername])
#         DIM3000.__init__(self, **kwargs)




