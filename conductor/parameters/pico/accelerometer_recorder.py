import json
import numpy as np
import os
import time

from twisted.internet.defer import inlineCallbacks

from conductor.parameter import ConductorParameter

class Recorder(ConductorParameter):
    autostart = True
    priority = 5
    call_in_thread = False
    
    data_filename = '{}.accelerometer_pico'
    nondata_filename = '{}/accelerometer_pico'
    pico_name  = 'accelerometer_pico'
    record_sequences = [
    	'all_off_pico',
        #'cavity_sweep',
        'gnd_cav',
        'cavity_sweep',
        'cavity_sweep_twice',
        'cavity_sweep_once_with_trigger',
        'cavity_sweep_once_with_trigger_nomeas',
        'cavity_sweep_once_with_trigger_homo',
        'cavity_sweep_once_with_trigger_homo_nopulse',
        'cavity_sweep_once_with_trigger_homo_ramsey',
        'cavity_sweep_once_with_trigger_homo_noprobe',
        'cavity_sweep_once_with_trigger_homo_ramsey_strong', 
        'cavity_sweep_once_with_trigger_homo_noprobe_old',
        'cavity_probe_with_trigger',
        'cavity_probe_with_trigger_noprobe',
        'cavity_probe_with_trigger_strong',
        'test_noprobe_withtrigger',   #Maybe the real 'test_noprobe_withtrigger' was the friends we made 
        			       #along the way
        'test_noprobe_Withtrigger',
        'test_noprobe_alt',
        'test_withprobe_withtrigger',
        'test_probe_alt',
       # 'dynamic_red_image_horizontal_mot_vertical_mot_fluor',
       # 'vrs_horizontal_mot_fluor_cav_perp',
       # 'gnd_horizontal_mot_fluor_vertical_mot'
        ]

    def initialize(self, config):
        super(Recorder, self).initialize(config)
        self.connect_to_labrad()
        request = {self.pico_name: {}}
        self.pico_cxn = self.cxn.accelerometer_pico
        self.pico_cxn.initialize_devices(json.dumps(request))
        print('Accelerometer pico initialized')
        self.pico_cxn.reset()
        print('Pico reset')


    def get_value(self):
        experiment_name = self.server.experiment.get('name')
        shot_number = self.server.experiment.get('shot_number')
        
        sequence = self.server.parameters.get('sequencer.sequence')
        previous_sequence = self.server.parameters.get('sequencer.previous_sequence')
        value = None
        if (experiment_name is not None) and (sequence is not None):
            point_filename = self.data_filename.format(shot_number)
            rel_point_path = os.path.join(experiment_name, point_filename)
        elif sequence is not None:
            rel_point_path  = self.nondata_filename.format(time.strftime('%Y%m%d'))
        ''' 
        if sequence.loop:
            if np.intersect1d(previous_sequence.value, self.record_sequences):
                value = rel_point_path
        '''
        if np.intersect1d(sequence.value, self.record_sequences):
            value = rel_point_path
        
        #value = self.nondata_filename.format(time.strftime('%Y%m%d'))
        return value
    '''
    @value.setter
    def value(self, x):
        pass
   ''' 
    def update(self):
        val = self.get_value()
        if val is not None:
            request = {self.pico_name: val}
            self.pico_cxn.record(json.dumps(request))
            #print('cavity probe picoscope requested')
Parameter = Recorder

