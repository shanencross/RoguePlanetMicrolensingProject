"""
dataRead_test.py
"""

import sys
import os
import numpy
import matplotlib.pyplot as plt

DATA_PARENT_DIR = "/science/robonet/rob/Operations/autodownload.2.0/"
YEAR = "2016"
SURVEY = "MOA"
DATA_DIR = os.path.join(os.path.join(DATA_PARENT_DIR, YEAR), SURVEY)

unknown_file = "2016-BLG-027"
xml_file = "2016-BLG-027-vot.xml"
dat_file = "KB160027.dat"
param_file = "KB160027.param"
notes_file = "KB160027.notes"

filenames = {"unknown": unknown_file, "xml": xml_file, "dat": dat_file, "param": param_file, "notes": notes_file}

filepaths = {}
for key in filenames:
	filename = filenames[key]
	filepath = os.path.join(DATA_DIR, filename)
	filepaths[key] = filepath
	
def test1():
	print DATA_DIR
	for key in filepaths:
		filepath = filepaths[key]
		print filepath

	with open(filepaths["dat"]) as datFile:
		times = []
		mags = []		
		mag_errs = []
		for line in datFile:
			# Skip commented lines
			if line[0] == "#":
				continue

			lineSplit = line.split()
			time = lineSplit[2]
			mag_err = lineSplit[1]
			mag = lineSplit[0]

			print "Time string:", time
			print "Magnitude string:", mag
			print "Magnitude error string:", mag_err
		
			times.append(float(time))
			mags.append(float(mag))
			mag_errs.append(float(mag_err))

		print "File:", filenames["dat"]
		#print "Times:", str(times)
		#print "Mags:", str(mags)
		#print "Mag errs:", str(mag_errs)
		plt.plot(times, mags, "ro")
		#plt.errorbar(times, mags, yerr = mag_errs)
		plt.axis([7415, 7445, 12, 26])
		plt.gca().invert_yaxis()
		plt.show()
	
		maxSlope = getMaxSlope(times, mags)

		if maxSlope > MINIMUM_SLOPE:
			print "TRIGGER"

def getMaxSlope(times, mags):
	gradients, times_output = calc_lc_gradient(times, mags)
	maximum_gradient = gradients.max()
	return maximum_gradient

def calc_lc_gradient( times, mag, interval ):
	gradients = []
	times_output = []
	for i in range( 0, len( event.t )-2, 2 ):
		if times[i] - times[i+1] < interval:
			gradients.append( ( mags[i] - mags[i+1] ) / ( times[i] - times[i+1] ) )
		times_output.append(times[i])
    return np.array( gradients ), np.array( times_output )

def main():
	test1()

if __name__ == "__main__":
	main()
