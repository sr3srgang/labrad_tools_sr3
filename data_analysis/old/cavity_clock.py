from data_analysis.simple_clock import *

def cavity_clock(settings, fig, ax, data_x, data_y):
	shot = settings['shot_number'] - shot_offset
	if shot > 3:
		gnd, exc, background, freq = import_pico_scan(settings['data_path'], settings['exp_name'], shot)
		gnd_sub = gnd - background
		exc_sub = exc - background
		if settings['isCleanUp'] == False:
			frac = calc_excitation(np.sum(gnd_sub[pico_shot_range]), np.sum(exc_sub[pico_shot_range]))
		else :
			#swap if cleanup
			frac = calc_excitation(np.sum(np.sum(exc_sub[pico_shot_range]), gnd_sub[pico_shot_range]))
		print(freq)
		add_to_plot(settings, exc, gnd, background, freq, frac, fig, ax)
		fig.tight_layout()
		#Add data to live plotter dataset
		if data_x is None:
			data_x = []
		if data_y is None:
			data_y = []
		data_x.append(freq)
		data_y.append(frac)
		#Add curve if 3/4 of way through scan
		if shot == int(.75* settings['maxShots']):
			add_gaussian(data_x, data_y, ax[0])
			pass
		return fig, data_x, data_y
