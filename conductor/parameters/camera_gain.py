from conductor.parameter import ConductorParameter
import numpy as np
class CameraGain(ConductorParameter):
    priority = 1
    autostart = True
    call_in_thread = True
    cameras = ['horizontal_mot', 'vertical_mot', 'cavity', 'cav_perp']
    current_vals = [None, None, None, None]
    
    def initialize(self, config):
        super(CameraGain, self).initialize(config)
        self.connect_to_labrad()
        #self.cxn.zuko_camera.init_camera()

    def update(self):
        for i in np.arange(len(self.cameras)):
            param_name = self.cameras[i] + '_gain'
            param = self.server.parameters.get(param_name)
            if param is not None:
                param_val = param.value
                if param_val != self.current_vals[i]:
                   # self.server._send_update({'update_' + param_name: param_val})
                    self.current_vals[i] = param_val
            #self.server._send_update({param_name: self.current_vals[i]})
Parameter = CameraGain 
