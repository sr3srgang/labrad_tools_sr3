import numpy as np
import os
from conductor.parameter import ConductorParameter
import time

class SetRecordPath(ConductorParameter):
    autostart = True
    priority = 2
    record_keyword = 'savePictures'
    align_keyword = 'align'
    fluorescence_keyword = 'fluor'
    absorption_keyword = 'absorption'
    data_filename = '{}_mako'
    camera_data_path = "K:/data/data"
    data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    align_name = 'align'

    def initialize(self, config):
        self.connect_to_labrad()
        print(self.cxn)
        self.cxn.zuko_camera.init_camera()

    def do_absorption_imaging(self, path):
        self.cxn.zuko_camera.get_frame(path + '_image.png')
        self.cxn.zuko_camera.get_frame(path + '_bright.png')
        self.cxn.zuko_camera.get_frame(path + '_dark.png')

    def do_fluorescence_imaging(self, path):
        self.cxn.zuko_camera.get_frame(path + '_fluorescence.png')

    def update(self):
        experiment_name = self.server.experiment.get('name')
        shot_number = self.server.experiment.get('shot_number')
        sequence = self.server.parameters.get('sequencer.sequence')
        if (experiment_name is not None) and (sequence is not None):
            if (self.record_keyword in str(experiment_name)) and ((self.fluorescence_keyword in str(sequence.value)) or (self.absorption_keyword in str(sequence.value))):
                point_filename = self.data_filename.format(shot_number)
                rel_point_path = os.path.join(self.camera_data_path, experiment_name, point_filename)
                #check if directory already exists; if not, make it
                experiment_directory = os.path.join(self.data_path, experiment_name)
                print(experiment_directory)
                if not os.path.isdir(experiment_directory):
                    os.makedirs(experiment_directory) 
                if self.absorption_keyword in str(sequence.value):
                    self.do_absorption_imaging(rel_point_path)
                else:
                    self.do_fluorescence_imaging(rel_point_path)
 
        elif sequence is not None:
            if self.align_keyword in str(sequence.value):
                time_string = time.strftime('%Y%m%d')
                today_path = os.path.join(self.camera_data_path, time_string, self.align_name)
               
               #check if today's data folder already exists; if not, make it
                today_data_dir = os.path.join(self.data_path, time_string)
                if not os.path.isdir(today_data_dir):
                    os.makedirs(today_data_dir)
                if self.absorption_keyword in str(sequence.value):
                    self.do_absorption_imaging(today_path)
                else:
                    self.do_fluorescence_imaging(today_path)

Parameter = SetRecordPath












