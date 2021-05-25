from pico.devices.picoscope.device import Picoscope


class CavityPico(Picoscope):
	picoscope_severname = 'appa_picoscope' 
	picoscope_serialnumber = 'IU888/0102'
	#Properties for data recording:
	picoscope_trigger_threshold = .5
	picoscope_timeout = 5000
	picoscope_duration = 2*20e-3
	picoscope_sampling_interval = 56e-9
	picoscope_n_capture = 1
	picoscope_channel_settings = {
		'A': {
		    'coupling': 'DC',
		    'VRange': 2.0,
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
	data_format = {'A': {'trigger':0,},}


Device = CavityPico
