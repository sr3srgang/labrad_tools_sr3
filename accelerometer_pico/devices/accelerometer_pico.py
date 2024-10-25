from pico.devices.picoscope.device_3000 import Picoscope


class CavityPico(Picoscope):
	picoscope_severname = 'appa_accelerometer_picoscope' 
	picoscope_serialnumber = 'IU888/0102'
	#Properties for data recording:
	picoscope_trigger_threshold = 2
	picoscope_timeout = 20000
	picoscope_duration =520e-3#2e-3#40e-3
	picoscope_sampling_interval = 2e-6#48e-9#16e-9#16e-9#16e-9#25e-6#16e-9
	picoscope_n_capture = 1#3
#	picoscope_resolution = 12   #8, 12, 13, 14, 15, 16
	picoscope_channel_settings = {
		'A': {
		    'coupling': 'DC',
		    'VRange': 0.2,
		    'probeAttenuation': 1.0,
		    'enabled': True,
		    },
		'B': {
		    'coupling': 'AC',
		    'VRange': 1.0,
		    'probeAttenuation': 1.0,
		    'enabled': False,
		    },
		'C': {
		    'coupling': 'AC',
		    'VRange': 1.0,
		    'probeAttenuation': 1.0,
		    'enabled': False,
		    },
		'D': {
		    'coupling': 'AC',
		    'VRange': 1.0,
		    'probeAttenuation': 1.0,
		    'enabled': False,
		    },
	}
	#first one used to work for single trigger
	data_format = {'A': {'gnd':0},}#, 'B':['acc']} #'exc':1}}#'test_new_trig': 1
	#data_format = {'A': {'gnd':0, 'exc':1},}
	

	#data_format = {'A': ['gnd', 'exc'],}
Device = CavityPico
