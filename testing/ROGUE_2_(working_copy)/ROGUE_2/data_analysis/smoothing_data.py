"""
smoothing_data.py
@author: Shanen Cross
"""

import numpy as np

def smooth_data(x_data, y_data, x_err_data=None, y_err_data=None, bin_size = 5):
	
	x_array = np.array(x_data)
	y_data = np.array(y_data)
	x_err_data = np.array(x_err_data)
	y_err_data = np.array(y_err_data)



	#DEBUG: Temp
	smooth_x_data = x_data
	smooth_y_data = y_data
	smooth_x_err_data = x_err_data
	smooth_y_err_data = y_err_data

	smoothed_data_dict = {"x": smooth_x_data, "y": smooth_y_data, "x_err": smooth_x_err_data, "y_err": smooth_y_err_data}

	return smoothed_data_dict
