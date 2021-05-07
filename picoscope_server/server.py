"""
### BEGIN NODE INFO
[info]
name = picoscope
version = 1.1
description = 
instancename = %LABRADNODE%_picoscope

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 947659321
timeout = 20
### END NODE INFO
"""
import h5py
import json
from labrad.server import LabradServer
from labrad.server import setting
import os
import time
from twisted.internet.defer import Deferred
from twisted.internet.reactor import callLater

from picoscope import ps3000a

from hardware_interface_server.server import HardwareInterfaceServer

class PicoscopeServer(HardwareInterfaceServer):
    """Provides access to picoscopes """
    name = '%LABRADNODE%_picoscope'

    def _get_available_interfaces(self):
        ps = ps3000a.PS3000a(connect=False)
        available_interfaces = ps.enumerateUnits()
        print(available_interfaces)
        ps.close()
        return available_interfaces
    
    def _get_open_interfaces(self):
        return self.interfaces.keys()

    def _open_interface(self, serial_number):
        open_interfaces = self._get_open_interfaces()
        if serial_number in open_interfaces:
            #raise InterfaceAlreadyOpen(serial_number)
            return
        try:
            ps = ps3000a.PS3000a(serial_number)
        except:
            raise InterfaceNotAvailable(serial_number)
        self.interfaces[serial_number] = ps
    
    def _close_interface(self, serial_number):
        ps = self._get_interface(serial_number)
        ps.close()
        del self.interfaces[serial_number]

    @setting(10, serial_number='s', channel='s', coupling='s', VRange='v', 
             VOffset='v', enabled='b', BWLimited='i', probeAttenuation='v')
    def set_channel(self, c, serial_number, channel='A', coupling='AC', 
                    VRange=2.0, VOffset=0.0, enabled=True, BWLimited=0,
                    probeAttenuation=1.0):
        print(serial_number)
        ps = self._get_interface(serial_number)
        ps.setChannel(channel, coupling, VRange, VOffset, enabled, BWLimited,
                      probeAttenuation)

    @setting(11, serial_number='s', sampleInterval='v', duration='v', 
             oversample='i', segmentIndex='i')
    def set_sampling_interval(self, c, serial_number, sampleInterval, duration, 
                              oversample=0, segmentIndex=0):
        ps = self._get_interface(serial_number)
        return ps.setSamplingInterval(sampleInterval, duration, oversample, 
                                      segmentIndex)

    @setting(12, serial_number='s', trigSrc='s', threshold_V='v', direction='s',
             delay='i', timeout_ms='i', enabled='b')
    def set_simple_trigger(self, c, serial_number, trigSrc, threshold_V=0, 
                           direction='Rising', delay=0, timeout_ms=100, 
                           enabled=True):
        ps = self._get_interface(serial_number)
        ps.setSimpleTrigger(trigSrc, threshold_V, direction, delay, timeout_ms, 
                            enabled)

    @setting(13, serial_number='s', noSegments='i')
    def memory_segments(self, c, serial_number, noSegments):
        ps = self._get_interface(serial_number)
        return ps.memorySegments(noSegments)

    @setting(14, serial_number='s', noOfCaptures='i')
    def set_no_of_captures(self, c, serial_number, noOfCaptures):
        ps = self._get_interface(serial_number)
        ps.setNoOfCaptures(noOfCaptures)
    
    @setting(15, serial_number='s', pretrig='v', segmentIndex='i')
    def run_block(self, c, serial_number, pretrig=0.0, segmentIndex=0):
        ps = self._get_interface(serial_number)
        ps.runBlock(pretrig, segmentIndex)
    
    @setting(16, serial_number='s')
    def is_ready(self, c, serial_number):
        ps = self._get_interface(serial_number)
        return ps.isReady()
    
    @setting(17, serial_number='s')
    def wait_ready(self, c, serial_number):
        ps = self._get_interface(serial_number)
        ps.waitReady()
    
    @setting(18, serial_number='s', channel='s', numSamples='i', startIndex='i',
             downSampleRatio='i', downSampleMode='i', segmentIndex='i')
    def get_data_v(self, c, serial_number, channel, numSamples=0, startIndex=0, 
                   downSampleRatio=1, downSampleMode=0, segmentIndex=0):
        ps = self._get_interface(serial_number)
        return ps.getDataV(channel, numSamples, startIndex, downSampleRatio,
                           downSampleMode, segmentIndex)

###    @setting(11, serial_number='s', duration='v', frequency='v')
##    def set_sampling_frequency(self, c, serial_number, duration, frequency):
##        X = frequency
##        Y = duration * frequency
##        ps = self._get_interface(serial_number)
##        response = ps.setSamplingFrequency(X, int(Y))
##        print 'set {} samples @ {} MHz'.format(response[1], response[0] / Y)
##
#    @setting(12, serial_number='s', source='s', threshold='v', timeout='i')
#    def set_simple_trigger(self, c, serial_number, source, threshold, timeout):
#        """ 
#        ARGS:
#            source: 'External' for external trigger
#            threshold: voltage for trigger threshold
#            timeout: time in ms for timeout. use negative number for infinite wait.
#        """
#        ps = self._get_interface(serial_number)
#        ps.setSimpleTrigger(trigSrc=source, threshold_V=threshold, 
#                            timeout_ms=timeout)
#
#    @setting(13, serial_number='s', n_segments='i', returns='i')
#    def memory_segments(self, c, serial_number, n_segments):
#        ps = self._get_interface(serial_number)
#        samples_per_segment = ps.memorySegments(n_segments)
#        return samples_per_segment
#
#    @setting(14, serial_number='s', n_captures='i')
#    def set_no_of_captures(self, c, serial_number, n_captures):
#        ps = self._get_interface(serial_number)
#        ps.setNoOfCaptures(n_captures)
#    
#    @setting(15, serial_number='s')
#    def run_block(self, c, serial_number):
#        ps = self._get_interface(serial_number)
#        ps.runBlock()
#    
#    @setting(16, serial_number='s')
#    def is_ready(self, c, serial_number):
#        ps = self._get_interface(serial_number)
#        return ps.isReady()
#    
#    @setting(17, serial_number='s')
#    def wait_ready(self, c, serial_number):
#        ps = self._get_interface(serial_number)
#        return ps.waitReady()
#
#
#    @setting(18, serial_number='s', channel='s', numSamples='i', segmentIndex='i')
#    def get_data_v(self, c, serial_number, channel, numSamples, segmentIndex):
#        ps = self._get_interface(serial_number)
#        
#    
#    def do_save_data(self, ps, rel_data_path, data_format):
#        while not ps.isReady():
#            time.sleep(0.05)
#        
#        data = {}
#        for channel, segments in data_format.items():
#            data[channel] = {name: ps.getDataV(channel, 50000, segmentIndex=num)
#                for name, num in segments.items()}
#        
#        abs_data_dir = os.join(self.data_path, os.path.dirname(rel_data_path))
#        if not os.path.isdir(abs_data_dir):
#            os.makedirs(abs_data_dir)
#
#        abs_data_path = os.join(self.data_path, rel_data_path)
#        with h5py.File(abs_data_path) as h5f:
#            for channel, segments in data.items():
#                grp = h5f.create_group(channel)
#                for name, data in segments.items():
#                    grp.create_dataset(name, data=data, compression='gzip')
#
#    @setting(17, serial_number='s', data_format_json='s', do_wait='b')
#    def get_data(self, c, serial_number, data_format_json, do_wait=False):
#        ps = self._get_interface(serial_number)
#        while not ps.isReady():
#            if not do_wait:
#                message = 'picoscope ({}) is not ready'.format(c['address'])
#                raise Exception(message)
#            else:
#                time.sleep(0.05)
#
#        data_format = json.loads(data_format_json)
#        response = {}
#        for channel, segments in data_format.items():
#            response[channel] = {}
#            for label, i in segments.items():
#                response[channel][label] =  ps.getDataV(channel, 50000, segmentIndex=i)
#
#        return json.dumps(response, default=lambda x: x.tolist())

Server = PicoscopeServer

if __name__ == '__main__':
    from labrad import util
    util.runServer(Server())
