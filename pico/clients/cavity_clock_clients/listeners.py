# Standard imports
import numpy as np

# Importing analysis code from data_analysis folder
from data_analysis.cavity_clock.read_data import *
from data_analysis.cavity_clock.helpers import *
from data_analysis.cavity_clock.MM_plotter_package import *

from pico.clients.cavity_clock_clients.params import *

from influxdb.influxdb_write import write_influxdb


def smart_append(data_x, data_y, x, y, name):
    if data_x is not None:
        data_x.append(x)
    if data_y is not None:
        data_y.append(y)
    try:
        # write_influxdb(name+'_x', x)
        write_influxdb(name, y)
        print('wrote {} to influxdb'.format(name))
    except Exception as e:
        print('InfluxDB server not happy:', e)


# CAVITY LISTENERS


def log_to_influxdb(influxdb_params):
    try:
        for (l, p) in influxdb_params:
            write_influxdb(l, p)
        print('logged all vals to influxdb')
    except Exception as e:
        print('InfluxDB server not happy:', e)


def get_influxdb_params(update, influxdb_log):
    for message_type, message in update.items():
        value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            influxdb_params = []
            for l in influxdb_log:
                n, x = get_metadata(
                    value, ax_name=l, str_end='.cavity_probe_pico_A.hdf5')
                influxdb_params.append((l, x))
            return influxdb_params


def filtered_cavity_time_domain(update, ax, seq):
    # MM 03222023 added listening for sweep params
    # print("sweep params: {}".format(sweep))
    # MM -03212023 written for compatibility with multiple triggers of ps6000a
    # MM05082023 determining window fits from sequence
    fixed_ixs = get_windows(seq)  # MM 20230508 added in "MM plotter package"
    ax.set_facecolor('xkcd:light pink')
    for message_type, message in update.items():
        value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            ax.clear()
            fits, _ = process_shot_var(value, fixed_ixs, ax=ax)
            ax.legend(labelcolor='k')
            ax.set_xlabel('Time (ms)', color='white')
            ax.set_ylabel('Homodyne Voltage', color='white')
            return True, fits, fixed_ixs
        else:
            return False, None, None


def sweep_to_f(update, ax, ax2, data_x, data_y, datums, sweep, fixed_ixs, ax_name=None):
    # MM 20230508 assuming run after filtered_cavity_time_domain w/ process_shot_var
    ax.set_facecolor('xkcd:light pink')
    # Extracting shot number
    for message_type, message in update.items():
        value = message.get('cavity_probe_pico')
        if message_type == 'record' and value is not None:
            n, x = get_metadata(
                value, ax_name=ax_name, str_end='.cavity_probe_pico_A.hdf5')
            if x is None:
                # default to shot num unless otherwise specified
                x = n
        else:
            return False, None, None
    if n > 1 and x is not None:
        # Setting numerical factors for converting sweep fitted times to cavity frequencies.
        mod_rate = 1.5e6  # 1.5e6  # MHz/V on 11/2 demod synthesizer
        t_range = .04  # .04  # set assuming 40 ms windows
        v_range = sweep[1] - sweep[0]
        # v_fixed = sweep[2]
        conv = v_range/t_range * mod_rate
        # t_fixed = (v_fixed - sweep[0])*t_range/v_range

        markers_fixed = ['.', '.', 'o', 'o', '.', '.', 'o', 'o']
        marker_swept = 'x'
        n_windows = len(fixed_ixs)
        dfs = np.zeros(n_windows)
        fixed_counter = 0
        swept_ixs = np.array(
            [i for i in np.arange(n_windows) if not fixed_ixs[i]])

        # [i for i in np.arange(n_windows) if not fixed_ixs[i]][-1]
        last_swept = swept_ixs[-1]
        # MM 20241213: log fit params of final sweep (presumed bare cav) to influxdb
        # bare_params = ['bare_amp', 'bare_fwhm', 'bare_c']
        params = ['delta', 'amp', 'fwhm', 'c']

        def RAM_DAC(v_range, t_range, sweep_start, last_swept):

            voltage = (last_swept[0]-.0005)*v_range/t_range + sweep_start
            return voltage

        def cav_resonance_voltage(v_range, t_range, sweep_start, last_swept, swept):
            voltage = (swept[0]-last_swept[0])*v_range/t_range + sweep_start
            return voltage

        DAC_voltage = RAM_DAC(v_range, t_range, sweep[0], datums[last_swept])
        try:
            write_influxdb('Cav_Resonance', DAC_voltage)
        except:
            1

        for k in np.arange(len(params)):
            p = params[k]
            smart_append(None, None, None,
                         datums[last_swept, k], 'bare_'+p)
            smart_append(None, None, None, datums[swept_ixs, k], 'all_' + p)

        for i in np.arange(n_windows):
            if i == n_windows - 1:
                c = c_bkgd
            else:
                c = cs[i % len(cs)]
            if not fixed_ixs[i]:
                dfs[i] = (datums[i, 0] - datums[last_swept, 0])*conv
                ax.plot(x, dfs[i], marker_swept, color=c, ms=9, mew=3)
                ax.plot(x, dfs[i], marker_swept, color='k', ms=9, mew=1)

                # print('plotter: {}'.format(dfs[i]))
            else:
                dfs[i] = datums[i, 0]  # just save voltages.
                ax2.plot(x, dfs[i], markers_fixed[fixed_counter % len(markers_fixed)],
                         color=c, alpha=.1)
                fixed_counter += 1
        smart_append(None, None, None, datums[fixed_ixs, 0], 'all_fixed')
        try:
            # print('all_freq')
            # print(datums[swept_ixs, 0])
            smart_append(None, None, None,
                         dfs[swept_ixs], 'all_freq_list')
        except:
            print('Wrong, all_freq')
        ax.set_ylabel('delta freq, sweep', color='white')
        # ax2.set_ylabel('delta v, fixed', color='white') #this is showing up on the wrong axis side by default?
        # smart_append(data_x, data_y, x, dfs, 'cav_fits')
        # print(dfs)
        data_x.append(x)
        data_y.append(dfs)
        return True, x, dfs, DAC_voltage, n
    else:
        return False, None, None, None, None


def exc_frac_cavity(ax, data_x, data_y, x, dfs, fixed_ixs, cav_detuning=2e6):
    ax.set_facecolor('xkcd:light pink')
    def f_to_n_delta(f, delta): return f*delta/5e3**2 * (1 + f/delta)
    def f_to_n(f): return f_to_n_delta(f, cav_detuning)
    swepts = dfs[np.logical_not(fixed_ixs)]
    g = f_to_n(swepts[0])
    e = f_to_n(swepts[1])
    exc_frac = e/(e + g)
    smart_append(data_x, data_y, x, exc_frac, 'cav_exc')
    smart_append(None, None, x, swepts[0], 'cav_freq_g')
    # print('influxdb: {}'.format(swepts[0]))
    smart_append(None, None, x, swepts[1], 'cav_freq_e')
    # data_x.append(x)
    # data_y.append(exc_frac)
    ax.plot(x, exc_frac, 'ok')


# CLOCK LISTENERS
def pmt_trace(update, ax):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('clock_pico')
        if message_type == 'record' and value is not None:
            gnd, exc, background, ts = get_pmt_data(value)
            ts *= 1e3  # Convert to ms
            ax.clear()
            ax.plot(ts, gnd, 'o', color='black')
            ax.plot(ts, background, 'o', color='gray')
            ax.plot(ts, exc, 'o', color='white', alpha=.6)
            ax.fill_between(ts[pico_shot_range], 0,
                            gnd[pico_shot_range], alpha=.4, color='grey')
            ax.set_xlabel('Time (ms)',  color='white')
            ax.set_ylabel('PMT Voltage', color='white')
            # ax.set_ylim((0, .2))
            # f = h5py.File(value)
            return True


def pmt_atom_number(update, ax, data_x, data_y, ax_name=None):
    ax.set_facecolor('xkcd:pinkish grey')
    for message_type, message in update.items():
        value = message.get('clock_pico')

        if message_type == 'record' and value is not None:
            shot_num, x_ax = get_metadata(value, ax_name=ax_name)
            if x_ax is None:
                # default to shot num unless otherwise specified
                x_ax = shot_num
            gnd, exc, background, _ = get_pmt_data(value)
            atom_num = np.sum((gnd + exc - 2*background)[pico_shot_range])
            num_gnd = np.sum((gnd - background)[pico_shot_range])
            num_exc = np.sum((exc - background)[pico_shot_range])

            # Don't display data before shot 2
            if shot_num is None or shot_num < 2:
                return False, None, None, None

            # Otherwise, plot and add to saved data
            # data_x.append(x_ax)
            # data_y.append(atom_num)
            smart_append(data_x, data_y, x_ax, atom_num, "pmt_num")
            smart_append(None, None, x_ax, num_gnd, "pmt_g")
            smart_append(None, None, x_ax, num_exc, "pmt_e")
            ax.plot(x_ax, num_gnd, 's', color='white',
                    fillstyle='none', zorder=3)
            ax.plot(x_ax, num_exc, 'd', color='white', zorder=2)
            ax.plot(x_ax, atom_num, 'o', color='k')
            return True, x_ax, num_gnd, num_exc

        else:
            return False, None, None, None


def pmt_exc_frac(ax, data_x, data_y, x, n_g, n_e):
    ax.set_facecolor('xkcd:pinkish grey')
    if x is not None:
        exc_frac = calc_excitation(n_g, n_e)
        ax.plot(x, exc_frac, 'o', color='k')
        ax.set_ylabel('Excitation fraction', color='white')
        smart_append(data_x, data_y, x, exc_frac, 'pmt_exc')
        # data_x.append(x)
        # data_y.append(exc_frac)
        return True
    else:
        return False
