from pico.devices.picoscope.device import Picoscope


class ClockPico(Picoscope):
    picoscope_severname = 'appa_clock_picoscope'
    picoscope_serialnumber = 'FP648/023'  # 'DU009/008'#'IU888/0102'
    # Properties for data recording:
    picoscope_trigger_threshold = 2
    picoscope_timeout = 10000  # 5000
    picoscope_duration = 1e-3
    picoscope_sampling_interval = 2e-6
    picoscope_n_capture = 3  # 2
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
    # data_format = {'A': {'trigger':0, },}#'test_new_trig': 1
    data_format = {'A': ['gnd', 'exc', 'bgd'], }


Device = ClockPico
