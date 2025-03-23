from rf.sg380 import *
from conductor.parameter import ConductorParameter

class Device(SG380):
    _vxi11_address = "192.168.1.16"


class CavEomSg380Amp(ConductorParameter):
    autostart = True
    priority = 3
    dev = None
    last_val = None
    
    phase_param_name = 'cav_eom_phase_sg380_R'
    last_phase = None
    #value = 130870000

    def initialize(self, config):
        super(CavEomSg380Amp, self).initialize(config)
        self.connect_to_labrad()
        self.dev = Device()
        if self.value is not None:
            self.dev.amplitude = self.value
        phase_param = self.server.parameters.get(self.phase_param_name)
        if phase_param is not None:
            self.dev.phase = phase_param

        

    def update(self):
        if self.value is not None:
        	if self.value != self.last_val:
           		self.dev.amplitude = self.value
           		#print(self.value)
           		print("SG380 (Cav) Amplitude is " + str(self.dev.amplitude))
			self.last_val = self.value
	phase_param = self.server.parameters.get(self.phase_param_name)
	#print(phase_param)
	#set phase. uses same connection to device and looks for updates to 'cav_eom_phase_sg380' specified as phase_param_name. note that phase wrapping can be tricky and isn't handled yet!!!
	if phase_param.value is not None:
		if phase_param.value != self.last_phase:
			self.dev.phase = phase_param.value
			new_val = self.dev.phase
			print("SG380 (Cav) Phase is " + str(new_val))
			self.last_phase = new_val
			#self.server.parameters.update({self.phase_param_name: new_val})

Parameter = CavEomSg380Amp
