class PicoscopeProxy(object):
    def __init__(self, server):
        self.server = server

    def PS3000a(self, serial_number):
        ps = PS3000aProxy(self.server, serial_number)
        return ps

class PS3000aProxy(object):
    def __init__(self, server, serial_number):
        self.server = server
        self.serial_number = serial_number
        print 1
        self.server.open_interface(self.serial_number)
        print 2

    def enumerateUnits(self):
        return self.server.get_available_interfaces()
    
    def getDataV(self, channel, numSamples=0, startIndex=0, downSampleRatio=1,
                 downSampleMode=0, segmentIndex=0):
        return self.server.get_data_v(self.serial_number, channel, numSamples, 
                                      startIndex, downSampleRatio, 
                                      downSampleMode, segmentIndex)

    def isReady(self):
        return self.server.is_ready(self.serial_number)

    def memorySegments(self, noSegments):
        return self.server.memory_segments(self.serial_number, noSegments)

    def runBlock(self, pretrig=0.0, segmentIndex=0):
        self.server.run_block(self.serial_number, pretrig, segmentIndex)

    def setChannel(self, channel='A', coupling='AC', VRange=2.0, VOffset=0.0, 
                   enabled=True, BWLimited=0, probeAttenuation=1.0):
        print channel, coupling, VRange, VOffset, enabled, BWLimited, probeAttenuation
        self.server.set_channel(self.serial_number, channel, coupling, VRange, 
                                VOffset, enabled, BWLimited, probeAttenuation)
    
    def setNoOfCaptures(self, noOfCaptures):
        self.server.set_no_of_captures(self.serial_number, noOfCaptures)
    
    def setSamplingInterval(self, sampleInterval, duration, oversample=0, 
                            segmentIndex=0):
        return self.server.set_sampling_interval(self.serial_number, 
                                                 sampleInterval, duration,
                                                 oversample, segmentIndex)

    def setSimpleTrigger(self, trigSrc, threshold_V=0, direction='Rising', 
                         delay=0, timeout_ms=100, enabled=True):
        self.server.set_simple_trigger(self.serial_number, trigSrc, threshold_V, 
                                       direction, delay, timeout_ms, enabled)

    def waitReady(self):
        self.server.wait_ready(self.serial_number)
