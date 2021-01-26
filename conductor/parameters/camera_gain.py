from conductor.parameter import ConductorParameter

class CameraGain(ConductorParameter):
    priority = 1
    autostart = True
    call_in_thread = True
    value = 30

    def initialize(self, config):
        super(CameraGain, self).initialize(config)
        self.connect_to_labrad()
        self.cxn.zuko_camera.init_camera()

    def update(self):
        if self.value is not None:
            self.cxn.zuko_camera.set_gain(self.value)

Parameter = CameraGain 
