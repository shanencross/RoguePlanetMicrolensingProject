"""
dataRead_test.py
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

DATA_PARENT_DIR = "/science/robonet/rob/Operations/autodownload.2.0/"
YEAR = "2016"
SURVEY = "MOA"
DATA_DIR = os.path.join(os.path.join(DATA_PARENT_DIR, YEAR), SURVEY)
MINIMUM_SLOPE = 10
EVENT_NAME= "2016-BLG-160"

if EVENT_NAME == "2016-BLG-027":
	unknown_file = "2016-BLG-027"
	xml_file = "2016-BLG-027-vot.xml"
	dat_file = "KB160027.dat"
	param_file = "KB160027.param"
	notes_file = "KB160027.notes"
	t0 = 7426.16

elif EVENT_NAME == "2016-BLG-100":
	unknown_file = "2016-BLG-100"
	xml_file = "2016-BLG-100-vot.xml"
	dat_file = "KB160100.dat"
	param_file = "KB160100.param"
	notes_file = "KB160100.notes"
	t0 = 7473.28

elif EVENT_NAME == "2016-BLG-053":
	unknown_file = "2016-BLG-053"
	xml_file = "2016-BLG-053-vot.xml"
	dat_file = "KB160053.dat"
	param_file = "KB160053.param"
	notes_file = "KB160053.notes"
	t0 = 7448.64

elif EVENT_NAME == "2016-BLG-160":
	print "160!"
	unknown_file = "2016-BLG-160"
	xml_file = "2016-BLG-160-vot.xml"
	dat_file = "KB160160.dat"
	param_file = "KB160160.param"
	notes_file = "KB160160.notes"
	t0 = 7511.31

else:
	unknown_file = "2016-BLG-027"
	xml_file = "2016-BLG-027-vot.xml"
	dat_file = "KB160027.dat"
	param_file = "KB160027.param"
	notes_file = "KB160027.notes"
	t0 = 7426.16

#current_time = datetime.utcnow()

time_lower_bound = t0 - 100
time_upper_bound = t0
mag_lower_bound = 14
mag_upper_bound = 20
gradient_lower_bound = -100
gradient_upper_bound = 100

filenames = {"unknown": unknown_file, "xml": xml_file, "dat": dat_file, "param": param_file, "notes": notes_file}

filepaths = {}
for key in filenames:
	filename = filenames[key]
	filepath = os.path.join(DATA_DIR, filename)
	filepaths[key] = filepath
	
def test1():
	#time_lower_bound = 7415
	#time_upper_bound = 7445

	print DATA_DIR
	for key in filepaths:
		filepath = filepaths[key]
		print filepath

	with open(filepaths["dat"]) as datFile:
		times_all = []
		mags_all = []		
		mag_errs_all = []
		for line in datFile:
			# Skip commented lines
			if line[0] == "#":
				continue

			lineSplit = line.split()
			time = lineSplit[2]
			mag_err = lineSplit[1]
			mag = lineSplit[0]

			#print "Time string:", time
			#print "Magnitude string:", mag
			#print "Magnitude error string:", mag_err
		
			times_all.append(float(time))
			mags_all.append(float(mag))
			mag_errs_all.append(float(mag_err))

		#print "File:", filenames["dat"]
		#print "Times:", str(times_all)
		#print "Mags:", str(mags_all)
		#print "Mag errs:", str(mag_errs_all)

		times = []
		mags = []
		mag_errs = []

		for i in xrange(len(times_all)):
			#print "Time: " + str(times_all[i])
			#print "Lower bound: " + str(time_lower_bound)
			#print "Upper bound: " + str(time_upper_bound)
			if times_all[i] < time_lower_bound:
				continue
			elif times_all[i] > time_upper_bound:
				break
			else:
				times.append(times_all[i])
				mags.append(mags_all[i])
				mag_errs.append(mag_errs_all[i])

		print
		#print "Times:", str(times)
		#print "Mags:", str(mags)
		#print "Mag errs:", str(mag_errs)
	
		gradients, gradientTimes, minTime, minTime2, minMag, minMag2, minSlope, maxTime, maxTime2, maxMag, maxMag2, maxSlope = getMinAndMaxSlope(times, mags)
		print "Min Slope Time:", minTime
		print "Min Slope Time 2:", minTime2
		print "Min Slope Mag:", minMag
		print "Min Slope Mag 2:", minMag2
		print "Min Slope:", minSlope
		calcMinSlope = (minMag2 - minMag) / (minTime2 - minTime)
		print "Calculated Min Slope:", calcMinSlope

		print "Max Slope Time:", maxTime
		print "Max Slope Time 2:", maxTime2
		print "Max Slope Mag:", maxMag
		print "Max Slope Mag 2:", maxMag2
		print "Max Slope:", maxSlope
		calcMaxSlope = (maxMag2 - maxMag) / (maxTime2 - maxTime)
		print "Calculated Max Slope:", calcMaxSlope
		if abs(minSlope) > MINIMUM_SLOPE:
			print "TRIGGER"
		else:
			print "NO trigger"
		#print list(reversed(sorted(times)))

		plt.plot(times, mags, "ro")
		#plt.errorbar(times, mags, yerr = mag_errs)
		plt.axis([time_lower_bound, time_upper_bound, mag_lower_bound, mag_upper_bound])
		plt.gca().invert_yaxis()
		plt.show()

		plt.plot(gradientTimes, gradients, "ro")
		#plt.errorbar(times, mags, yerr = mag_errs)
		plt.axis([time_lower_bound, time_upper_bound, gradient_lower_bound, gradient_upper_bound])
		plt.gca().invert_yaxis()
		plt.show()

def getMinAndMaxSlope(times, mags, interval=float("inf")):
	#print "Times: " + str(times)
	#print "Mags: " + str(mags)
	gradients, times_output = calc_lc_gradient(times, mags, interval)
	minimum_gradient = gradients.min()
	minimum_index = gradients.argmin() * 2
	minimum_time = times[minimum_index]
	try:
		minimum_time2 = times[minimum_index + 1]
	except IndexError as ex:
		"There is no time following the time for the minimum gradient value"
		print ex
		minimum_time2 = minimum_time

	minimum_mag = mags[minimum_index]
	try:
		minimum_mag2 = mags[minimum_index + 1]
	except IndexError as ex:
		print "There is magnitude following the magnitude for the minimum gradient value"
		print ex
		minimum_mag2 = minimum_mag

	maximum_gradient = gradients.max()
	maximum_index = gradients.argmax() * 2
	maximum_time = times[maximum_index]
	try:
		maximum_time2 = times[maximum_index + 1]
	except IndexError as ex:
		"There is no time following the time for the maximum gradient value"
		print ex
		maximum_time2 = maximum_time
	maximum_mag = mags[maximum_index]
	try:
		maximum_mag2 = mags[maximum_index + 1]
	except IndexError as ex:
		print "There is magnitude following the magnitude for the maximum gradient value"
		print ex
		maximum_mag2 = maximum_mag

	return gradients, times_output, minimum_time, minimum_time2, minimum_mag, minimum_mag2, minimum_gradient, \
		   maximum_time, maximum_time2, maximum_mag, maximum_mag2, maximum_gradient

def calc_lc_gradient( times, mags, interval = float("inf")):
	print "times: " + str(times)
	print "mags: " + str(mags)
	gradients = []
	times_output = []
	for i in range( 0, len( times )-2, 2 ):
		#print "Interval:", interval
		#print "Time difference:", (times[i+1] - times[i])
		#print "Times 2 - Time 1: " + str(times[i+1] - times[i])
		#print "Interval: " + str(interval)
		if times[i+1] - times[i] < interval:
			gradients.append( ( mags[i+1] - mags[i] ) / ( times[i+1] - times[i] ) )
		times_output.append(times[i])
	return np.array( gradients ), np.array( times_output )

def main():
	test1()

if __name__ == "__main__":
	main()
