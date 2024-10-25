from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter

class TransportSweep(ConductorParameter):
    autostart = True
    priority = 2
    default_frequency = 110.0e6
    other_frequency = 111.174e6
    default = True
    #offset = 1e6
    ramp_rate =-128#0#2**15# -8

    def initialize(self,config):
        self.connect_to_labrad()
        #self.request =  {'ad9956_transport': {'start': self.default_frequency, 'stop': self.default_frequency+self.offset, 'rate': self.ramp_rate} }
        #self.cxn.rf.linear_ramps(json.dumps(self.request))
        #print(self.cxn.rf.frequencies())
        #print 'hr_demod_frequency init\'d with rr: {}'.format(self.ramp_rate)
        print('Initialized')
    
    def update(self):
        if self.value is not None:
            print('transport param called')
            if self.default:
                freq = self.default_frequency
            else:
                freq = self.default_frequency #self.other_frequency
            self.default = not self.default
            request = {'ad9956_transport': {'start': freq, 'stop': freq + 1e6, 'rate': self.ramp_rate} }
            self.cxn.rf.linear_ramps(json.dumps(request))
            print(request)
            '''
#            min_freq = min([self.value, self.dark_frequency])
#            max_freq = max([self.value, self.dark_frequency])
#            yield self.cxn.rf.linear_ramp(min_freq, max_freq, self.ramp_rate)
            min_freq = min([self.value, self.value + self.dark_offset])
            max_freq = max([self.value, self.value + self.dark_offset])
            request =  {'ad9956_0': {'start': min_freq, 'stop': max_freq, 'rate': self.ramp_rate} }
            initial_request =  {'ad9956_0': {'start': self.default_frequency, 'stop': self.default_frequency+self.offset, 'rate': self.ramp_rate} }
            '''
            #self.cxn.rf.linear_ramps(json.dumps(self.request))
        

Parameter = TransportSweep
