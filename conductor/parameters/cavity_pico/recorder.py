import json
import numpy as np
import os
import time

from twisted.internet.defer import inlineCallbacks

from conductor.parameter import ConductorParameter

class Recorder(ConductorParameter):
    autostart = False
    priority = -1
    data_filename = '{}.cavity_pico'
    nondata_filename = '{}/cavity_pico'
    pmt_name = 'cavity_pico'
    record_sequences = [
        'dynamic_red_image_horizontal_mot_vertical_mot_fluor_cav_perp_cavity'
        ]

    def initialize(self, config):
        super(Recorder, self).initialize(config)
        self.connect_to_labrad()
        request = {self.pmt_name: {}}
        self.cxn.pmt.initialize_devices(json.dumps(request))
        print('Cavity pico initialized')


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
            rel_point_path = self.nondata_filename.format(time.strftime('%Y%m%d'))
            
        if sequence.loop:
            if np.intersect1d(previous_sequence.value, self.record_sequences):
                value = rel_point_path
        elif np.intersect1d(sequence.value, self.record_sequences):
            value = rel_point_path

        return value
    '''
    @value.setter
    def value(self, x):
        pass
   ''' 
    def update(self):
        val = self.get_value()
        if val is not None:
            request = {self.pmt_name: val}
            self.cxn.pmt.record(json.dumps(request))

Parameter = Recorder

