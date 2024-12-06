class FrequencyOutOfBoundsError(Exception):
    pass

class AmplitudeOutOfBoundsError(Exception):
    pass

#see https://www.thinksrs.com/downloads/pdfs/manuals/SG380m.pdf for doc


class SG380(object):
    _frequency_range = (1e6, 2e9) #in Hz
    _amp_range = (-60, 5) #in dBm
    _vxi11_address = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if 'vxi11' not in globals():
            global vxi11
            import vxi11
        self._inst = vxi11.Instrument(self._vxi11_address)

   
    @property
    def frequency(self):
        command = 'FREQ?'
        ans = self._inst.ask(command)
        return float(ans)
    
    @frequency.setter
    def frequency(self, frequency):
        if frequency < min(self._frequency_range) or frequency > max(self._frequency_range):
            raise FrequencyOutOfBoundsError(frequency)
        #print frequency
        command = 'FREQ {}'.format(frequency)
        self._inst.write(command)
    
    #MM 20241125, add amplitude control (for cav eom driver). queries/sets amplitude in dBm
    
    @property
    def amplitude(self):
        command = 'AMPR?'
        ans = self._inst.ask(command)
        return float(ans)
        
    @amplitude.setter
    def amplitude(self, amp):
        if amp < min(self._amp_range) or amp > max(self._amp_range):
            raise AmplitudeOutOfBoundsError(amp)
        command = 'AMPR {}'.format(amp)
        self._inst.write(command)

    @property
    def phase(self):
        command = 'PHAS?'
        ans = self._inst.ask(command)
        return float(ans)
        
    @phase.setter
    def phase(self, amp):
        command = 'PHAS {}'.format(amp)
        self._inst.write(command)
       
class SG380Proxy(SG380):
    _vxi11_servername = None

    def __init__(self, cxn=None, **kwargs):
        if cxn == None:
            import labrad
            cxn = labrad.connect()
        from vxi11_server.proxy import Vxi11Proxy
        global vxi11
        vxi11 = Vxi11Proxy(cxn[self._vxi11_servername])
        SG380.__init__(self, **kwargs)




