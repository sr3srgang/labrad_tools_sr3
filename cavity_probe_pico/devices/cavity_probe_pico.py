from pico.devices.picoscope.device_6000a import Picoscope


class CavityPico(Picoscope):
	picoscope_severname = 'appa_cavity_picoscope' 
	picoscope_serialnumber = 'IW990/0033'#'FP648/023' 'FP648/023'#'DU009/008'#'IU888/0102'
	#Properties for data recording:
	picoscope_trigger_threshold = .1
	picoscope_timeout = 5000# in ms
	picoscope_duration =.52
	picoscope_sampling_interval = 2e-6#2e-6#48e-9#16e-9#16e-9#16e-9#25e-6#16e-9
	picoscope_n_capture = 1#3
#	picoscope_resolution = 12   #8, 12, 13, 14, 15, 16
	picoscope_channel_settings = {
		'A': {
		    'coupling': 'DC',
		    'VRange': .2,
		    'probeAttenuation': 1.0,
		    'enabled': True,
		    },

	}
	#first one used to work for single trigger
	data_format = {'A': ['gnd']}#, 'B':['acc']} #'exc':1}}#'test_new_trig': 1


	#data_format = {'A': ['gnd', 'exc'],}
Device = CavityPico
'''
		'B':{
		    'coupling': 'DC',
		    'VRange': 5,
		    'probeAttenuation': 1.0,
		    'enabled': True
		    }
		    '''
