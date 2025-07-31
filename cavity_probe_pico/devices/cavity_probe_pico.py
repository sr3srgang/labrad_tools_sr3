from pico.devices.picoscope.device_6000a import Picoscope


class CavityPico(Picoscope):
    picoscope_severname = 'appa_cavity_picoscope'
    # 'FP648/023' 'FP648/023'#'DU009/008'#'IU888/0102'
    picoscope_serialnumber = 'IW990/0033'
    # Properties for data recording:
    picoscope_trigger_threshold = .1
    picoscope_timeout = 10000  # in ms
    picoscope_duration = .04 #.04  # .52 #20230313 MM updated for multiple capture testing
    picoscope_sampling_interval = 1e-6  # 2e-6
    # 2e-6#48e-9#16e-9#16e-9#16e-9#25e-6#16e-9
    picoscope_n_capture = 13 #7
# picoscope_resolution = 12   #8, 12, 13, 14, 15, 16
    picoscope_channel_settings = {
        'A': {
            'coupling': 'DC',
            'VRange': 1,
            'probeAttenuation': 1.0,
            'enabled': True,
        },
        'B': {
            'coupling': 'DC',
            'VRange':  1,
            'probeAttenuation': 1.0,
            'enabled': True,
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
    # first one used to work for single trigger
    # data_format = {'A': ['00', '01', '02', '03', '04', '05', '06'],
    #                'B': ['00', '01', '02', '03', '04', '05', '06']}
    # data_format = {'A': ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10'],
    #                'B': ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10']}
    data_format = {'A': ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'], 'B': [
        '00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']}


Device = CavityPico
