from pico.devices.picoscope.device_5000 import Picoscope


class CavityPico(Picoscope):
	picoscope_severname = 'appa_cavity_picoscope' 
	picoscope_serialnumber = 'IV953/0134'# 'FP648/023'#'DU009/008'#'IU888/0102'
	#Properties for data recording:
	picoscope_trigger_threshold = 2
	picoscope_timeout = 5000
	picoscope_duration = 40e-3
	picoscope_sampling_interval = 16e-9
	picoscope_n_capture = 1#3
#	picoscope_resolution = 12   #8, 12, 13, 14, 15, 16
	picoscope_channel_settings = {
		'A': {
		    'coupling': 'DC',
		    'VRange': 0.05,
		    'probeAttenuation': 1.0,
		    'enabled': True,
		    },
		'B': {
		    'coupling': 'DC',
		    'VRange': 1.0,
		    'probeAttenuation': 1.0,
		    'enabled': False,
		    },
		'C': {
		    'coupling': 'DC',
		    'VRange': 1.0,
		    'probeAttenuation': 1.0,
		    'enabled': False,
		    },
		'D': {
		    'coupling': 'DC',
		    'VRange': 1.0,
		    'probeAttenuation': 1.0,
		    'enabled': False,
		    },
	}
	data_format = {'A': {'trigger':0, },}#'test_new_trig': 1
	#data_format = {'A': {'gnd':0, 'exc':1, 'bgd':2,},}


Device = CavityPico
