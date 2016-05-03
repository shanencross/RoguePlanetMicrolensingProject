"""
smoothing_data.py
@author: Shanen Cross
"""

import numpy as np

def smooth_data(x_data, y_data, x_err_data=None, y_err_data=None, step_size=.1, bin_size = 5):
	
	x_array = np.array(x_data)
	y_data = np.array(y_data)

	if x_err_data is not None:
		x_err_data = np.array(x_err_data)
	if y_err_data is not None:
		y_err_data = np.array(y_err_data)

	print x_err_data
	print y_err_data
	print x_err_data is None


	print "Smooth0"
	if x_err_data is None or y_err_data is None:
		smoothed_data_dict = smooth_no_errors(x_data, y_data, step_size, bin_size)
		print "Smooth1"
	
	else:
		smoothed_data_dict = smooth_with_errors(x_data, y_data, x_err_data, y_err_data, step_size, bin_size)
		print "Smooth2"

	#DEBUG: Temp
	"""
	smooth_x_data = x_data
	smooth_y_data = y_data
	smooth_x_err_data = x_err_data
	smooth_y_err_data = y_err_data
	smoothed_data_dict = {"x": smooth_x_data, "y": smooth_y_data, "x_err": smooth_x_err_data, "y_err": smooth_y_err_data}
	Z"""
	
	return smoothed_data_dict


def smooth_no_errors(x_data, y_data, step_size=.1, bin_size=1):

	smooth_x_data, smooth_y_data = get_moving_average(x_data, y_data, step_size, bin_size)
	smoothed_data_dict = {"x": smooth_x_data, "y": smooth_y_data}

	return smoothed_data_dict

def get_moving_average(x,y,step_size=.1,bin_size=1):

	#Code taken from: http://stackoverflow.com/questions/18517722/weighted-moving-average-in-python
    bin_centers  = np.arange(np.min(x),np.max(x)-0.5*step_size,step_size)+0.5*step_size
    bin_avg = np.zeros(len(bin_centers))

    for index in xrange(0,len(bin_centers)):
        bin_center = bin_centers[index]
        items_in_bin = y[(x>(bin_center-bin_size*0.5) ) & (x<(bin_center+bin_size*0.5))]
        bin_avg[index] = np.mean(items_in_bin)

    return bin_centers,bin_avg

def smooth_with_errors(x_data, y_data, x_err_data, y_err_data, step_size=.1, bin_size=1):
	#Debug: Temp
	return None
