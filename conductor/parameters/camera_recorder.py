import numpy as np
import os
from conductor.parameter import ConductorParameter
import time

class CameraRecorder(ConductorParameter):
    autostart = True
    priority = -1
    
    #Keywords to determine if/where we save the pictures
    record_keyword = 'savePictures'
    fluorescence_keyword = 'fluor'
    absorption_keyword = 'absorption'

    #Keywords to set which camera we're using
    cameras = ['horizontal_mot', 'vertical_mot', 'cavity', 'cav_perp']

    camera_data_path = "K:/data/data" #Path to data folders on zuko, which runs the camera servers
    data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data') #Path to data folders on appa (conductor)
    data_filename = "{}_{}_{}"

    def initialize(self, config):
        super(CameraRecorder, self).initialize(config)
        self.connect_to_labrad()
        
    def do_absorption_imaging(self, path):
        return [path + '_image.png', path + '_bright.png', path + '_dark.png']

    def do_fluorescence_imaging(self, path):
        return [path + '_fluorescence.png']

    def update(self):
    	sequences = self.server.parameters.get('sequencer.sequence')
    	for s in sequences.value: #loop over subsequences
		for cam in self.cameras:
		    if  cam in s: #check if camera is in this sequence name
		        paths = self.get_paths(cam, s)
		        print(paths)
		        self.cxn.camera.record(cam, paths)
    
    def safe_in(self, str1, str2):
        return str2 is not None and str1 in str2
  

    def get_paths(self, cam, sequence):
        experiment_name = self.server.experiment.get('name')
        shot_number = self.server.experiment.get('shot_number')
        if self.safe_in(self.record_keyword, experiment_name):
            dir_path = os.path.join(self.data_path, experiment_name)
            rel_point_path = os.path.join(self.camera_data_path, experiment_name, self.data_filename.format(cam, sequence, shot_number))
        else:
            time_string = time.strftime('%Y%m%d')
            dir_path = os.path.join(self.data_path, time_string)
            rel_point_path = os.path.join(self.camera_data_path, time_string, cam)
        #Check if directory already exists; if not, make it
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
        #Do fluorescence or absorption imaging:
        if self.absorption_keyword in str(sequence):
            return self.do_absorption_imaging(rel_point_path)
        elif self.fluorescence_keyword in str(sequence):
            return self.do_fluorescence_imaging(rel_point_path)
            
Parameter = CameraRecorder












