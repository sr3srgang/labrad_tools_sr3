from collections import deque

from device_server.device import DefaultDevice
from picoscope_server.proxy import PicoscopeProxy

class Picoscope(DefaultDevice):
    picoscope_servername = None
    picoscope_serialnumber = None
    picoscope_duration = None
    picoscope_frequency = None
    picoscope_n_capture = None
    picoscope_trigger_threshold = None # [V]
    picoscope_timeout = None # [ms]
    picoscope_channel_settings = {}

    n_samples = None

    records = {}
    record_names = deque([])
    max_records = 100
    
    
    def initialize(self, config):
        super(Picoscope, self).initialize(config)
        self.connect_to_labrad()
        self.picoscope_server = self.cxn[self.picoscope_servername]
        ps3000a = PicoscopeProxy(self.picoscope_server)
        ps = ps3000a.PS3000a(self.picoscope_serialnumber)

        for channel_name, channel_settings in self.picoscope_channel_settings.items():
            ps.setChannel(channel_name, **channel_settings)
        response = ps.setSamplingInterval(self.picoscope_sampling_interval, 
                                          self.picoscope_duration)
        self.n_samples = response[1]
        print 'sampling interval:', response[0]
        print 'number of samples:', response[1]
        print 'max samples:', response[2]
        ps.setSimpleTrigger('External', self.picoscope_trigger_threshold,
                            timeout_ms=self.picoscope_timeout)
        ps.memorySegments(self.picoscope_n_capture)
        ps.setNoOfCaptures(self.picoscope_n_capture)
        
        self.ps = ps

#        self.picoscope_server.reopen_interface(self.picoscope_serialnumber)
#        for channel, settings in self.picoscope_channel_settings.items():
#            self.picoscope_server.set_channel(self.picoscope_serialnumber, 
#                                              channel, settings['coupling'], 
#                                              settings['voltage_range'], 
#                                              settings['attenuation'], 
#                                              settings['enabled'])
#        self.picoscope_server.set_sampling_frequency(self.picoscope_serialnumber, 
#                                                     self.picoscope_duration, 
#                                                     self.picoscope_frequency)
#        self.picoscope_server.set_simple_trigger(self.picoscope_serialnumber, 
#                                                 'External', 
#                                                 self.picoscope_trigger_threshold, 
#                                                 self.picoscope_timeout)
#        self.picoscope_server.memory_segments(self.picoscope_serialnumber,
#                                              self.picoscope_n_capture)
#        self.picoscope_server.set_no_of_captures(self.picoscope_serialnumber,
#                                                 self.picoscope_n_capture)

    def record(self, data_path):
        pass

    def retrive_records(self, record_name):
        if type(record_name).__name__ == 'int':
            record_name = self.record_names[record_name]
        if record_name not in self.records:
            message = 'cannot locate record: {}'.format(record_name)
            raise Exception(message)
        record = self.records[record_name]
        record['record_name'] = record_name
        return record
