from conductor.parameter import ConductorParameter
import os, np
#MM 20250731
#read in value of bare cavity dac offset from pico client
#to be used with cav_aom_813_rigol in setting up a RAM servo for cavity lock
class BareDACVoltage(ConductorParameter):
    autostart = True
    priority = 5 #just needs to be higher htan cav_aom_813_rigol
   
    data_filename = 'bare_dac_voltage_{}.txt'
    data_directory = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')

    record_sequences = [
    	'cav_sweep', 
    	'cav_sweep_bare'	
        ]
        
    def initialize(self, config):
        super(BareDACVoltage, self).initialize(config)
        self.connect_to_labrad()

    def find_path(self):
    	experiment_name = self.server.experiment.get('name')
        shot_number = self.server.experiment.get('shot_number')
        
        sequence = self.server.parameters.get('sequencer.sequence')
        previous_sequence = self.server.parameters.get('sequencer.previous_sequence')
        
        if (experiment_name is not None) and (sequence is not None):
            point_filename = self.data_filename.format(shot_number)
            rel_point_path = os.path.join(experiment_name, point_filename)
        
        if len(np.intersect1d(sequence.value, self.record_sequences)) > 0:# is not None:
            return os.path.join(data_dirctory, rel_point_path)
    	
    def update(self):
        path = self.find_path()
        print(path)
        if path is not None:
            try:
                with open(path, 'r') as file:
                    val = file.read()
                print(val)
                self.value = val
            except:
                pass

Parameter = BareDACVoltage
