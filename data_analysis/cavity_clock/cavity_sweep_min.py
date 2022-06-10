#Helper functions for cavity listeners
from pico.clients.cavity_clock_clients.params import *
from scipy.signal import find_peaks

def get_res_dips(t_avg, max_fs, t_range):
   in_range = (t_avg > t_range[0]) & (t_avg < t_range[1])
   n_points = len(t_avg[in_range])
   ix_0, _ = find_peaks(-max_fs[in_range, 0], distance = n_points)
   ix_1, _ = find_peaks(-max_fs[in_range, 1], distance = n_points)
   #print('found peaks:')
   #print(t_avg[in_range][ix_0], t_avg[in_range][ix_1])
   return t_avg[in_range][ix_0][0], t_avg[in_range][ix_1][0]
   
def get_vrs(t_avg, max_fs, ax, t_range = t_range_emp, scan_rate = scan_rate_emp, t_cross = crossing_emp):
    t0, t1 = get_res_dips(t_avg, max_fs, t_range = t_range)
    if ax is not None:
        ax.plot(t0*1e3, np.min(max_fs[:, 0]), 'ok')
        ax.plot(t1*1e3, np.min(max_fs[:, 1]), 'ok')
    t_elapsed = (t0 + t1)/2 - t_cross
    return t_elapsed*scan_rate*2
