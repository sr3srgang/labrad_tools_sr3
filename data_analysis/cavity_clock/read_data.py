# Functions to help read in pmt/pd data to do listener analysis
import numpy as np
import os
import json
import h5py

# Reading in metadata about the experiment being run:


def get_expt(update):
    for message_type, message in update.items():
        value = message.get('clock_pico')
        if value is None:
            value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            head, _ = os.path.split(value)
            day, expt = os.path.split(head)
            # print('Expt folder:')
            # print(os.path.join(head, day))
            return expt, os.path.join(head, day)
        else:
            return None, None


def get_shot_num(path, str_end='.clock_pico.hdf5'):
    # str_end = '.clock_pico.hdf5'
    head, tail = os.path.split(path)
    split_str = tail.partition(str_end)
    try:
        shot_num = int(split_str[0])
    except:
        shot_num = None
    return shot_num, head


def get_metadata(path, ax_name, str_end='.clock_pico.hdf5'):
    shot_num, folder_path = get_shot_num(path, str_end)
    if shot_num is not None and ax_name is not None:
        f_name = "{}.conductor.json".format(shot_num-1)
        path = os.path.join(folder_path, f_name)
        f = open(path)
        c_json = json.load(f)
        val = c_json[ax_name]
    else:
        val = None
    return shot_num, val


def sweep_params(update):
    for message_type, message in update.items():
        if message_type == 'params':
            return (message.get('low'), message.get('high'), message.get('fixed')), message.get('sequence')
        else:
            return None, None


# Reading in pico files for pmt
# Cavity fitting functions located in MM_plotter_package
""" def get_cavity_data(abs_data_path, trace='gnd'):
    # print(abs_data_path)
    with h5py.File(abs_data_path) as h5f:
        data = np.array(h5f[trace])
        # self.test = np.array(h5f['test_new_trig'])
        # print(self.test)
        ts = np.array(h5f['time'])
    return data, ts """


def get_pmt_data(abs_data_path):
    f = h5py.File(abs_data_path)
    gnd = np.array(f['gnd'])
    exc = np.array(f['exc'])
    background = np.array(f['bgd'])
    ts = np.array(f['time'])
    return gnd, exc, background, ts
