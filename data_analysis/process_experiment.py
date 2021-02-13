import json, os, glob
import numpy as np
import data_analysis.imaging_tools as it

conductor_file = '{}.conductor.json'
camera_file_format = '{}_*.png'
path_to_data = it.path_to_data

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
	return file_names, param_vals
	
	
def bin_1D_exp_loop(folder, param_name, first_file, n_files):
	file_names, param_vals = get_files(folder, first_file, n_files, [param_name])
	ts = param_vals[:, 0] #name from case of red mot TOF, where independent param is time. 
	unique_ts = set(ts)
	n_times = len(unique_ts) 
	
	#Fit integer number of reps
	n_reps = int(np.floor(n_files/n_times))
	#Formatting files according to 1D variable loop
	files_binned = np.reshape(file_names[0:n_reps*n_times], (n_reps, n_times))
	
	return files_binned, unique_ts, ts

def fit_1d_exp_loop(script, n_params, files_binned, show_plot = False):
	#ASSUMES BACKGROUND FILE IS LAST IN EACH REP	
	#initialize data arrays
	(n_reps, n_times) = np.shape(files_binned)
	popts = np.zeros((n_reps, n_times - 1, n_params))
	perrs = np.zeros((n_reps, n_times - 1, n_params))
	
	for i in np.arange(n_reps):
		for j in np.arange(n_times - 1):
			popts[i, j, :], perrs[i, j, :] = script(files_binned[i, j], background_file = files_binned[i, -1], show_plot = show_plot)
	
	return popts, perrs

def red_TOF(folder, first_file, n_files, show_plot = False):
	files_binned, unique_ts, ts = bin_1D_exp_loop(folder, 'sequencer.rTOF', first_file, n_files)
	if not(ts[0] == min(unique_ts)):
		print('bad starting point!!')
	else:
		popts, perrs = fit_1d_exp_loop(it.fit_gaussian_2D_real, 7, files_binned, show_plot = show_plot)
		return(popts, perrs)
	

def show_MOT_image(file_name):
			
		
		
