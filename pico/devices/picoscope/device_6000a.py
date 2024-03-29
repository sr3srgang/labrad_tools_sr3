from device_server.device import DefaultDevice
from picoscope import ps6000a
import os
import json
import h5py
import time
import numpy as np
import matplotlib.pyplot as plt
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
		ps = ps6000a.PS6000a(self.picoscope_serialnumber)
		print('Found pico!')
		for x in np.arange(1, 4):
			ps.setChannel(x, enabled=False)
		for channel_name, channel_settings in self.picoscope_channel_settings.items():
            		ps.setChannel(channel_name, **channel_settings)
            	
            	response = ps.setSamplingInterval(self.picoscope_sampling_interval, 
                                          self.picoscope_duration)
        	print 'sampling interval:', response[0]
        	print 'number of samples:', response[1]
        	print 'max samples:', response[2]
        	self.n_samples = response[1]
        	#MM 10130105: ACTUALLY uses Aux channel, hardcoded in as 1001 in low-level as per device spec. 
        	ps.setSimpleTrigger('A', self.picoscope_trigger_threshold, timeout_ms=self.picoscope_timeout) 
        	ps.memorySegments(self.picoscope_n_capture)
        	ps.setNoOfCaptures(self.picoscope_n_capture)
        	self.ps = ps
        	print('set to trigger')
        	self.ps.runBlock(pretrig=0.0, segmentIndex=0)
		#self.ps.waitReady()
		
	def reset(self):
		self.ps.stop()
		self.ps.runBlock(pretrig=0.0, segmentIndex=0)	
		print('reset: ran block')
		#self.ps.waitReady()
	
	def record(self, rel_data_path):
		self.recordMultipleTriggers(rel_data_path)
	'''
	def set_max_V(self, V_new):
		self.picoscope_channel_settings['A']['VRange'] = V_new
		self.ps.setChannel('A', **self.picoscope_channel_settings['A'])
		print('Pico channel A max voltage set to {} V'.format(V_new))	
	'''	
	def recordMultipleTriggers(self, rel_data_path):
		print('called!')
		self.ps.waitReady()
		print('ready')
		t0 = time.time()
    
		print(self.data_format.items())
		n_channels = len(self.data_format.items())
		for ix_c in np.arange(n_channels):
			channel, segments = self.data_format.items()[ix_c] #MM 20230313assuming for
			(data_raw, numSamples, overflow) = self.ps.getDataRawBulk(channel=channel) #bulk for multiple triggers
			print(data_raw.shape)
			print(channel)
			dataV = self.ps.rawToV(channel, data_raw)
			print(np.shape(dataV))
			data = {}
			data[channel] = {}
			for i in np.arange(len(segments)):
				data[channel][segments[i]] = dataV[i, :]
		
			#Save data. Data file path comes from conductor parameter, where condition for temporarily or permanently saving data is set. 
			#Check if today's data folder already exists; if not, make it
			time_string = time.strftime('%Y%m%d')
			dir_path = os.path.join(self.data_path, time_string)
			if not os.path.isdir(dir_path):
			    os.makedirs(dir_path)
			
			#Save data
			raw_data = data[channel]
			ts = np.arange(self.n_samples)*self.picoscope_sampling_interval
			
			#MM 20240118 modified to record data from multiple channels
			path_end = '_{}.hdf5'.format(channel)
			h5py_path = os.path.join(self.data_path, rel_data_path + path_end)
			if ix_c == 0:
				server_path = h5py_path
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
		message = {'record': {self.name: server_path}}
		self.server._send_update(message)
		
		self.ps.stop()
		self.ps.setNoOfCaptures(self.picoscope_n_capture)
		self.ps.runBlock()
		
	def recordSingleTrigger(self, rel_data_path):
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
		print(self.data_format.items())
		channel, segments = self.data_format.items()[0]
		(data_raw, numSamples, overflow) = self.ps.getDataRaw(channel=channel) #NOT bulk in this case
		dataV = self.ps.rawToV(channel, data_raw)
		print(np.shape(dataV))
		data = {}
		'''
		for channel, segments in self.data_format.items():
			data[channel] = {}
			for i in np.arange(len(segments)):
				label = segments[i]
				print(dataV.shape)
				data[channel][label] = dataV[i, :]
		'''
		
		data[channel] = {}
		data[channel][segments[0]]= dataV

		
		#Save data. Data file path comes from conductor parameter, where condition for temporarily or permanently saving data is set. 
		#print("Time acquiring: {}".format(tf - t0))
		#Check if today's data folder already exists; if not, make it
		time_string = time.strftime('%Y%m%d')
		dir_path = os.path.join(self.data_path, time_string)
		if not os.path.isdir(dir_path):
		    os.makedirs(dir_path)
		
		#Save data
		raw_data = data[channel]
		ts = np.arange(self.n_samples)*self.picoscope_sampling_interval
		h5py_path = os.path.join(self.data_path, rel_data_path + '.hdf5')
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
		
		
		
		
		

		
