        
        '''
        #MM 041322 turn off heterodyne buttons and add homodyne buttons
        #Add fft client option to left cavity trace
        self.fft_left = QPushButton(self)
        self.fft_left.setText('FFT on click')
        self.fft_left.move(525, 372)
        self.fft_left.clicked.connect(self.show_fft)
        
        
        self.set_param = QPushButton(self)
        self.set_param.setText('IQ params')
        self.set_param.move(1145, 372)
        '''
        #MM 20221214 turn off cav buttons
        '''
        self.fit_toggle = QPushButton(self)
        self.fit_toggle.move(525, 372)
        self.fit_toggle.setAutoDefault(False)
        self.fit_settings = ["Fit off", "Q response", "Mean"]
        self.do_fit = len(self.fit_settings) - 1
        self.toggle_fit() #Initialize with fit off
        self.fit_toggle.pressed.connect(self.toggle_fit)
        
        self.cav_detuning = QLineEdit(self)
        self.cav_detuning.setText("NaN")
        self.cav_detuning.move(1145, 372)
        self.cav_detuning.returnPressed.connect(self.set_detuning)
        self.current_cav_detuning = None #no detuning specified yet on start-up
        self.cav_detuning.setVisible(False)
        
        #MM 051922: client for setting time windows for spin measurements
        #JOHN UPDATE DEFAULT PARAM VALS HERE
        self.current_dark_time = 100e-6
        t_dark = self.current_dark_time 
        
        
        self.current_time_settings = {'t1_a': 0.1e-3,
        't1_b': 39.5e-3,
        't2_a': 48.1e-3,
        't2_b': 88e-3,
        't3_a': 89e-3 +t_dark,
        't3_b': 89e-3+39e-3+t_dark,
        't4_a': 136e-3+t_dark,
        't4_b': 175e-3+t_dark}
        
        self.time_settings={'t1_start': .1e-3, 't_window': 39e-3, 't_between': 9e-3, 't_dark': 100e-6, 'cav_detuning': np.nan}
        
        self.set_windows = QPushButton(self)
        self.set_windows.setText('Set windows')
        self.set_windows.move(350, 372)
        self.set_windows.pressed.connect(self.clicked_set_windows)
        
   def make_time_windows(self):
        ts = {
        't1_a': self.time_settings['t1_start'],
        't1_b': self.time_settings['t1_start'] + self.time_settings['t_window'],
        't2_a': self.time_settings['t1_start'] + self.time_settings['t_window'] + self.time_settings['t_between'],
        't2_b': self.time_settings['t1_start'] + 2* self.time_settings['t_window'] + self.time_settings['t_between'],
        't3_a': self.time_settings['t1_start'] + 2* self.time_settings['t_window'] + self.time_settings['t_between'] + self.time_settings['t_dark'],
        't3_b': self.time_settings['t1_start'] + 3* self.time_settings['t_window'] + self.time_settings['t_between'] + self.time_settings['t_dark'],
        't4_a': self.time_settings['t1_start'] + 3* self.time_settings['t_window'] + 2*self.time_settings['t_between'] + self.time_settings['t_dark'],
        't4_b': self.time_settings['t1_start'] + 4* self.time_settings['t_window'] + 2*self.time_settings['t_between'] + self.time_settings['t_dark']}
        return ts
            
        '''
        
        
        #MM 06102022 commented old zuko version in merge conflict with toph
'''
<<<<<<< HEAD
pico_shot_range = np.arange(10, 25)
freq_offset = 116.1e6
from scipy.signal import find_peaks
from sys import platform

crossing_emp = .00154
t_range_emp = [.007, .017]
scan_rate_emp = 1e6/(20e-3) #1MHz/20 ms
def get_cavity_data(abs_data_path, trace = 'gnd'):
    if platform == 'win32':
        abs_data_path = 'K:/' + path[15:]
    with h5py.File(abs_data_path) as h5f:
        data = np.array(h5f[trace])
        #self.test = np.array(h5f['test_new_trig'])
        #print(self.test)
        ts = np.array(h5f['time'])
    return data, ts
=======
'''
