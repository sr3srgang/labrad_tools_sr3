import json, os, glob
import numpy as np
import imaging_tools as it

conductor_file = '{}.conductor.json'
camera_file_format = '{}_*.png'

def get_files(folder, first_file, n_files, key_params):
	n_params = len(key_params)
	param_vals = np.zeros((n_files, n_params))
	file_names = []
	f_ixs = np.arange(first_file, first_file + n_files)
	c_ixs = f_ixs + 1
	
	for i in np.arange(n_files):
    		global_conductor_path = os.path.join(path_to_data, folder, conductor_file.format(c_ixs[i]))
   		with open(global_conductor_path) as f:
        	c_json = json.loads(f.read())
        	for n in np.arange(n_params):
            		param_vals[i, n] = c_json[key_params[n]]
    		camera_file = os.path.join(path_to_data, folder, camera_file_format.format(f_ixs[i]))
    
    		matching_files = glob.glob(camera_file)
    		if len(matching_files) > 1:
        		print('Improper data formatting!!')
        		print(matching_files)
    		file_names.append(matching_files[0])
