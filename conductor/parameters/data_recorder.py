import copy
import json
import os
import time

from twisted.internet import reactor

from conductor.parameter import ConductorParameter


class DataRecorder(ConductorParameter):
    autostart = True
    priority = -1
    data_directory = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    data_filename = '{}.conductor.json'
    call_in_thread = False

    def update(self):
        experiment_name = self.server.experiment.get('name')
        shot_number = self.server.experiment.get('shot_number')

        if experiment_name is not None:
            experiment_directory = os.path.join(self.data_directory, experiment_name)
            if not os.path.isdir(experiment_directory):
                os.makedirs(experiment_directory)
        
            point_filename = self.data_filename.format(shot_number)
            point_path = os.path.join(experiment_directory, point_filename)
            
            ti = time.time()
            parameter_values = self.server._get_parameter_values(request={}, all=True)
            print time.time() - ti
            reactor.callInThread(self._save_json, point_path, copy.deepcopy(parameter_values))
    
    def _save_json(self, point_path, parameter_values):
       with open(point_path, 'w') as outfile:
           json.dump(parameter_values, outfile, default=lambda x: None)
    
    
Parameter = DataRecorder
