import json
import h5py
import numpy as np
import os
from scipy.optimize import curve_fit
import time

from twisted.internet.reactor import callInThread

from pmt.devices.picoscope.device import Picoscope


class CavityPico(Picoscope):
    autostart = True
    picoscope_servername = 'appa_picoscope'
    picoscope_serialnumber = 'DU009/008'#'IU888/0102'
    picoscope_duration = 20e-3 #20 ms interval
    picoscope_sampling_interval = 20e-9
    picoscope_frequency = 100e6
    picoscope_n_capture = 1
    picoscope_trigger_threshold = .5 # [V]
    picoscope_timeout = 5000 #-1 # [ms]
    verbose = True
    recording = False

    picoscope_channel_settings = {
        'A': {
            'coupling': 'DC',
            'VRange': 1.0,
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

    data_format = {
        'A': {
            'trigger': 0,
            #'exc': 1,
            #'bac': 2,
            },
        }
    
    data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')


    def record(self, rel_data_path):
        self.recording_name = rel_data_path
        if self.recording:
            raise Exception('already recording')
        callInThread(self.do_record_data, rel_data_path)
    
    def do_record_data(self, rel_data_path):
        self.recording = True
        self.ps.runBlock()
        self.ps.waitReady()

        data = {}
        for channel, segments in self.data_format.items():
            data[channel] = {}
            for label, i in segments.items():
#                data[channel][label] = self.ps.getDataV(channel, 50000, 
#                                                        segmentIndex=i)
                data[channel][label] = self.ps.getDataV(channel, self.n_samples,
                                                        segmentIndex=i)
        self.recording = False

        #Save data. Data file path comes from conductor parameter, where condition for temporarily or 
        #permanently saving data is set. 

        #Check if today's data folder already exists; if not, make it
        time_string = time.strftime('%Y%m%d')
        dir_path = os.path.join(self.data_path, time_string)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

        #Save data
        raw_data = data['A']
	h5py_path = os.path.join(self.data_path, rel_data_path + '.hdf5')
        h5f = h5py.File(h5py_path, 'w')
        for k, v in raw_data.items():
            h5f.create_dataset(k, data=np.array(v), compression='gzip')
        h5f.close()
        
        #Send the file path out to the client, so it can redraw
        message = {'record': {self.name: h5py_path}}
        self.server._send_update(message)

Device = CavityPico
