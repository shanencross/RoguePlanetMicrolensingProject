"""
evaluateData.py
@author: Shanen Cross
"""

"""
Input: Event name with survey prefix, and boolean for whether same event has been detected by other survey.

Get folder dir from event name. 
Root dir: /science/robonet/rob/Operations/autodownload.2.0/
Plus current year: /2016/
Plus survey prefix: /MOA/ or /OGLE
to get complete dir: /science/robonet/rob/Operations/autodownload.2.0/2016/MOA or /science/robonet/rob/Operations/autodownload.2.0/OGLE

If MOA prefix, 
Convert event name to filename for event. MOA-2016-BLG-001 -> KB20160001.dat. OGLE-2016-BLG-0001 -> OB20160001.dat.

Data filepath is complete dir + file name.

Read in data file. From each non-commented line, acquire time, magnitude, and magnitude error, and append to corresponding list. Format will be different depending on survey, so what column corresponds to what value will change depending on survey value, determined during getting the folder dir.

Can we assume the times are listed sequentially? If not, sort times, and somehow sort magnitudes and errors alongside them (not sure how to do this).

Get current time. Shrink lists to include only data points from before current time and after 48 hours (2 days) before current time.

If there are fewer than 2 data points remaining (i.e. one), return False. (? Or should we look further back in time?)

Calculate list of gradients of every two adjacent data points. Find the most negative (i.e. minimum) slope, since brighter points have lower magnitudes, and we're looking for sharp brightness increases, i.e. sharp drops in magnitude value. Also get time of slope

If slope is negative and its absolute value is greater than our threshold (default: 10), return True. Otherwise, return False.

[Alternative logic: If slope is less than our threshold, which is a negative number (default: -10), return True. Otherwise, return False. Or we could have our threshold variable be positive but make it negative in the calculate.]

Output: Boolean for whether maximum slope in the past 48 hours is large enough.
"""

import sys
import os
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

import loggerSetup

#create and set up filepath and directory for logs -
#log dir is subdir of script
LOG_DIR = os.path.join(sys.path[0], "logs/evaluateDataLog")
LOG_NAME = "evaluateDataLog"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
logger = loggerSetup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT)

DATA_PARENT_DIR = "/science/robonet/rob/Operations/autodownload.2.0/"
CURRENT_TIME = str(datetime.utcnow())
SLOPE_THRESHOLD = 10
TEST_EVENT_NAME= "2016-BLG-053"

time_lower_bound = t0 - 30
time_upper_bound = t0 + 30
mag_lower_bound = 14
mag_upper_bound = 20
gradient_lower_bound = -100
gradient_upper_bound = 100

filenames = {"unknown": unknown_file, "xml": xml_file, "dat": dat_file, "param": param_file, "notes": notes_file}

def getEventMaxRise(eventName, daysAgo = 2):
	surveyName = getEventSurvey(eventName)
	filepath = getEventFilepath(eventName, surveyName)

	with open(filepath, "r") as dataFile:
		dataPoints = readInData(dataFile)
		sort(dataPoints, key=lambda k: k["time"])
		currentDay = getTimeInHJD(CURRENT_TIME)

		dataPoints_trimmed = trimDataPoints(dataPoints, currentDay, daysAgo)
		maxRise = getDataMaxRise(dataPoints_trimmed)

def getDataMaxRise(dataPoints, interval=float("inf")):
	gradientPoints = calc_lc_gradient(dataPoints)

	return maxRise = max(gradientPoints, key=lambda k: k["mag"])

def calc_lc_gradient( dataPoints, interval = float("inf")):

	gradientDicts = []
	for i in range( 0, len( dataPoints )-2, 2 ):
		dataPoint_1 = dataPoints[i]
		dataPoint_2 = dataPoints[i+1]
		time_1 = dataPoint_1["time"]
		time_2 = dataPoint_2["time"]
		mag_1 = dataPoint_1["mag"]
		mag_2 = dataPoint_2["mag"]

		if time_2 - time_1 < interval:
			gradient = ( mag_2 - mag_1 ) / ( times_2 - times_1 ) )
			gradientTime = time_1
			gradientDict = {"gradient": gradient, "time:", gradientTime}
			gradientDicts.append(gradientDict)

	return gradientDicts



def getTimeInHJD(timeUTC):
	return ""

def trimDataPoints(dataPoints, currentDay, daysAgo):
	dayLowerBound = currentDay - daysAgo

	newDataDicts = []
	for dataPoint in xrange(len(dataPoints)):
		time = dataPoint["time"]
		mag = dataPoint["mag"]
		mag_err = dataPoint["mag_err"]

		if time < dayLowerBound:
			continue
		elif time > currentDay:
			break
		else:
			newDataDict = {"time": time, "mag": mag, "mag_err": mag_err}
			newDataDicts.append(newDataDict)

	return newDataDicts
		
def readInData(dataFile):
	#times = []
	#mags = []		
	#mag_errs = []
	dataDicts = []
	time_index = 2
	mag_index = 0
	mag_err_index = 1

	for line in datFile:
		# Skip commented lines
		if line[0] == "#":
			continue

		lineSplit = line.split()
		time = lineSplit[time_index]
		mag_err = lineSplit[mag_err_index]
		mag = lineSplit[mag_index]

		#print "Time string:", time
		#print "Magnitude string:", mag
		#print "Magnitude error string:", mag_err
		
		#times.append(float(time))
		#mags.append(float(mag))
		#mag_errs.append(float(mag_err))
		dataDict = {"time": float(time), "mag": float(mag), "mag_errs": mag_errs}
		dataDicts.append(dataDict)

	return dataDicts

def getEventSurvey(eventName):
	if eventName[:3] == "MOA":
		surveyName = "MOA"

	elif eventName[:4] == "OGLE":
		surveyName = "OGLE
	else:
		logger.warning("Event name, %s, does not begin with MOA or OGLE survey name. Assuming name is a 2016 MOA name without survey prefix." % eventName)
		surveyName = "MOA"

	return surveyName

def getEventFilepath(eventName, surveyName):
	if surveyName] == "MOA":
		eventFilename = "KB"
		eventName_short = eventName[4:]

	elif surveyName == "OGLE":
		eventFilename = "OB"
		eventName_short = eventName[5:]
	else:
		logger.warning("Event name, %s, does not begin with MOA or OGLE survey name. Assuming name is a 2016 MOA name without survey prefix." % eventName)
		eventYear = "2016"
		eventFilename = "KB"
		eventName_short = eventName

	eventYear = eventName_short[:4]
	filename += eventYear[2:] + "%04d" % int(eventName_short[9:])
	fileExtension = ".dat"
	eventFilepath = os.path.join(os.path.join(DATA_PARENT_DIR, eventYear), filename + fileExtension)
	
	return eventFilepath


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
		if abs(minSlope) > SLOPE_THRESHOLD:
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

def main():
	test1()

if __name__ == "__main__":
	main()
