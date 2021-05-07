import json
import h5py
import numpy as np
import os
from scipy.optimize import curve_fit
import time

from twisted.internet.reactor import callInThread

from pmt.devices.picoscope.device import Picoscope

TAU = 2.3e4
def fit_function(x, a):
    return a * np.exp(-x / TAU)

class BluePMT(Picoscope):
    raw_data_path = '/home/srgang/K/data/pmt_data' #Single data file is overwritten every cycle to save HD space
    autostart = True
    picoscope_servername = 'appa_picoscope'
    picoscope_serialnumber = 'IU888/0102'
    picoscope_duration = 0.025e-3
    picoscope_sampling_interval = 20e-9
    picoscope_frequency = 100e6
    picoscope_n_capture = 3
    picoscope_trigger_threshold = 2 # [V]
    picoscope_timeout = -1 # [ms]
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
            'gnd': 0,
            'exc': 1,
            'bac': 2,
            },
        }

    p0 = [1]
    
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

        raw_data = data['A']
        raw_sums = {label: sum(raw_counts) for label, raw_counts in raw_data.items()}
        raw_fits = {}

        b = np.mean(raw_data['bac'])
        for label, raw_counts in raw_data.items():
            counts = np.array(raw_counts)[500:] - b
            #popt, pcov = curve_fit(fit_function, range(len(counts)), counts, p0=self.p0)
            #raw_fits[label] = popt[0]

        tot_sum = raw_sums['gnd'] + raw_sums['exc'] - 2 * raw_sums['bac']
        frac_sum = (raw_sums['exc'] - raw_sums['bac']) / tot_sum
        #tot_fit = raw_fits['gnd'] + raw_fits['exc'] - 2 * raw_fits['bac']
        #frac_fit = (raw_fits['exc'] - raw_fits['bac']) / tot_fit
        tot_fit = tot_sum
        frac_fit = frac_sum



        processed_data = {
            'frac_sum': frac_sum,
            'tot_sum': tot_sum,
            'frac_fit': frac_fit,
            'tot_fit': tot_fit,
            }
        abs_data_dir = os.path.join(self.data_path, os.path.dirname(rel_data_path))
        if not os.path.isdir(abs_data_dir):
            os.makedirs(abs_data_dir)
    
        abs_data_path = os.path.join(self.data_path, rel_data_path)         
        if self.verbose:
            print "saving processed data to {}".format(abs_data_path)

        json_path = abs_data_path + '.json'
        with open(json_path, 'w') as outfile:
            json.dump(processed_data, outfile, default=lambda x: x.tolist())
        
        #h5py_path = abs_data_path + '.hdf5'
	h5py_path = self.raw_data_path + '.hdf5' #Overwrite file every time to save HD space
        h5f = h5py.File(h5py_path, 'w')
        for k, v in raw_data.items():
            h5f.create_dataset(k, data=np.array(v), compression='gzip')
        h5f.close()
        
        """ temporairly store data """
        if len(self.record_names) > self.max_records:
            oldest_name = self.record_names.popleft()
            if oldest_name not in self.record_names:
                _ = self.records.pop(oldest_name)
        self.record_names.append(rel_data_path)
        self.records[rel_data_path] = processed_data
        
        message = {'record': {self.name: rel_data_path}}
        self.server._send_update(message)

Device = BluePMT
