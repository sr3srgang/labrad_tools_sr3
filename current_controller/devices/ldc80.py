import numpy as np
import time


class LDC80(object):
    _visa_address = None
    _pro8_slot = None
    _current_range = (0.0, np.inf)
    _relock_stepsize = 0
    _locked_threshold = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if 'visa' not in globals():
            global visa
            import visa
        rm = visa.ResourceManager()
        self._inst = rm.open_resource(self._visa_address)

    def _write_to_slot(self, command):
        slot_command = ':SLOT {};'.format(self._pro8_slot)
        self._inst.write(slot_command + command)
    
    def _query_to_slot(self, command):
        slot_command = ':SLOT {};'.format(self._pro8_slot)
        response = self._inst.query(slot_command + command)
        return response
    
    @property
    def current(self):
        command = ':ILD:SET?'
        response = self._query_to_slot(command)
        return float(response[9:])
    
    @current.setter
    def current(self, request):
        min_current = self._current_range[0]
        max_current = self._current_range[1]
        request = sorted([min_current, request, max_current])[1]
        command = ':ILD:SET {}'.format(request)
        self._write_to_slot(command)
    
    @property
    def is_locked(self):
        if self.power > self._locked_threshold:
            return True
        else:
            return False
    
    @property
    def power(self):
        command = ':POPT:ACT?'
        response = self._query_to_slot(command)
        power = float(response[10:])
        return power

    def relock(self):
        current = self.current
        self.current = current + self._relock_stepsize
        time.sleep(0.2)
        self.current = current

    @property
    def state(self):
        command = ':LASER?'
        response = self._query_to_slot(command)
        if response.strip() == ':LASER ON':
            return True
        elif response.strip() == ':LASER OFF':
            return False

    @state.setter
    def state(self, state):
        if state:
            command = ':LASER ON'
        else:
            command = ':LASER OFF'
        self._write_to_slot(command)

class LDC80Proxy(LDC80):
    _visa_servername = None

    def __init__(self, cxn=None, **kwargs):
        from visa_server2.proxy import VisaProxy
        if cxn == None:
            import labrad
            cxn = labrad.connect()
        global visa
        visa_server = cxn[self._visa_servername]
        visa = VisaProxy(visa_server)
        LDC80.__init__(self, **kwargs)
