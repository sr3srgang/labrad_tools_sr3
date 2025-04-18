from device_server.device import DefaultDevice
from picoscope import ps5000a
import os
import json
import h5py
import time
import numpy as np
import matplotlib.pyplot as plt

#MM updated 051222 to enable multiple channels
class Picoscope(DefaultDevice):
	picoscope_severname = None #what labrad will look for this device as
	picoscope_serialnumber = None
	#Data format (see cavity_pico for examples):
	picoscope_channel_settings = None 
	data_format = None
	#Properties for data recording:
	picoscope_trigger_threshold = None #V
	picoscope_timeout = None #ms
	picoscope_duration = None #s
	picoscope_sampling_interval = None #s
	picoscope_n_capture = None #How many triggers to listen for/how many sequential timeseries will be saved
	
	data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
	#data_path = os.path.join('/home/srgang/H/data/', 'data')
	
	
	def initialize(self, config):
		super(Picoscope, self).initialize(config)
		self.connect_to_labrad()
		self.init_pico()
		
	def init_pico(self):
		ps = ps5000a.PS5000a(self.picoscope_serialnumber)
		#except:
		#	DeviceInitializationFailed(serial_number)
		
		for channel_name, channel_settings in self.picoscope_channel_settings.items():
            		ps.setChannel(channel_name, **channel_settings)
            	
            	response = ps.setSamplingInterval(self.picoscope_sampling_interval, 
                                          self.picoscope_duration)
        	print 'sampling interval:', response[0]
        	print 'number of samples:', response[1]
        	print 'max samples:', response[2]
        	self.n_samples = response[1]
        
        	ps.setSimpleTrigger('External', self.picoscope_trigger_threshold, timeout_ms=self.picoscope_timeout)
        	print('set to trigger')
        	ps.memorySegments(self.picoscope_n_capture)
        	ps.setNoOfCaptures(self.picoscope_n_capture)
        	self.ps = ps
        	#self.ps.runBlock(pretrig=0.0, segmentIndex=0)
		#self.ps.waitReady()
		
	def reset(self):
		self.ps.stop()
		self.ps.runBlock(pretrig=0.0, segmentIndex=0)	
		#self.ps.waitReady()
	'''
	def set_max_V(self, V_new):
		self.picoscope_channel_settings['A']['VRange'] = V_new
		self.ps.setChannel('A', **self.picoscope_channel_settings['A'])
		print('Pico channel A max voltage set to {} V'.format(V_new))	
	'''	
	def record(self, rel_data_path):
		print('called!')
		self.ps.waitReady()
		print('ready')
		t0 = time.time()
		'''
		data = {}
        	for channel, segments in self.data_format.items():
            		data[channel] = {}
            		
            		for i in np.arange(3):
            			label = segments[i]
            			print(label)
                		data[channel][label] = self.ps.getDataV(channel, self.n_samples, segmentIndex=i)
                		print(data[channel][label])
				print('acquired')
		'''      
		#Read in data from pico
		(data_raw, numSamples, overflow) = self.ps.getDataRawBulk()


		#Format according to data_format from child class
		data = {}
		for channel, segments in self.data_format.items():
			data[channel] = {}
			for i in np.arange(len(segments)):
				label = segments[i]
				dataV = self.ps.rawToV(channel, data_raw)
				data[channel][label] = dataV[i, :]

		
		#Save data. Data file path comes from conductor parameter, where condition for temporarily or permanently saving data is set. 
		#print("Time acquiring: {}".format(tf - t0))
		#Check if today's data folder already exists; if not, make it
		time_string = time.strftime('%Y%m%d')
		dir_path = os.path.join(self.data_path, time_string)
		if not os.path.isdir(dir_path):
		    os.makedirs(dir_path)
		
		#Save data
		ts = np.arange(self.n_samples)*self.picoscope_sampling_interval
		for channel, _ in self.data_format.items():
		    raw_data = data[channel]		    
		    h5py_path = os.path.join(self.data_path, rel_data_path + '_' + channel + '.hdf5')
		    if channel == 'A':
		        message = {'record': {self.name: h5py_path}}
		    else:
		        message = {'record_other':{self.name:h5py_path}}
		    self.server._send_update(message)
		    try:
			h5f = h5py.File(h5py_path, 'w')
			for k, v in raw_data.items():
		    		h5f.create_dataset(k, data=np.array(v), compression='gzip')
		    	h5f.create_dataset('time', data = np.array(ts), compression = 'gzip')
			h5f.close()
		    except:
			print('Unable to save pico file!')
        	
        	print('data saved')
        	tf = time.time()
        	print("Elapsed time recording: {}".format(tf - t0))
		message = {'record': {self.name: h5py_path}}
		self.server._send_update(message)
		
		self.ps.stop()
		self.ps.runBlock()
		
		
		
		
		

		
