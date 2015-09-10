import sys
from bs4 import BeautifulSoup
import requests
requests.packages.urllib3.disable_warnings()
from datetime import datetime

#default values
EVENT_NAME = "2015-BLG-1812"
IS_OGLE_NAME = True
REVERSE_SURVEY_LOOKUP = False

MAX_MAG_ERR = 0.7

def main():
	#set default values if cmd line args are not present
	eventName = EVENT_NAME
	isOGLEname = IS_OGLE_NAME
	reverseSurveyLookup = REVERSE_SURVEY_LOOKUP

	if len(sys.argv) > 1:
		eventName = sys.argv[1]

	if len(sys.argv) > 2:
		if sys.argv[2] == "OGLE":
			isOGLEname = True
		elif sys.argv[2] == "MOA":
			isOGLEname = False

	if len(sys.argv) > 3:
		if sys.argv[3] == "normal":
			reverseSurveyLookup = False
		elif sys.argv[3] == "reverse":
			reverseSurveyLookup = True

	if reverseSurveyLookup:
		if isOGLEname:
			eventName = OGLEtoMOA(eventName)
			print
			printMOAvalues(eventName)
		else: #MOA NAME
			eventName = MOAtoOGLE(eventName)
			print
			printOGLEvalues(eventName)
	else:
		if isOGLEname:
			printOGLEvalues(eventName)
		else: #MOA NAME
			printMOAvalues(eventName)

def printMOAvalues(eventName):
	MOA_values = getMOAvalues(eventName)
	"""
	print "URL: %s" % MOA_values[0]
	print "tMax (JD): %s" % getString(MOA_values[1])
	print "tE: %s" % getString((MOA_values[2])
	print "u0: %s" % getString(MOA_values[3])
	print "Light curve plot:", MOA_values[4]
	if mag_values is not None:
		print "mag: %s" % getString(MOA_values[5])
	print "Assessment: %s" % MOA_values[6]
	print "Remarks: %s" % MOA_values[7]
	"""

def getMOAvalues(eventName):
	if eventName is None:
		print "No event found for %s" % eventName
		return
	ID = getID(eventName)
	if ID is None:
		print "No ID found for event %s" % eventName
		return

	nameURL = "https://it019909.massey.ac.nz/moa/alert2015/display.php?id=" + ID
	request = requests.get(nameURL, verify=False)
	page = request.content
	soup = BeautifulSoup(page, 'lxml')

	microTable = soup.find(id="micro").find_all('tr')

	tMax_line = microTable[0].find_all('td')
	tMaxJD = float(tMax_line[2].string.split()[1])
	tMax_splitString = tMax_line[4].string.split()
	tMaxJD_err = float(tMax_splitString[0])
	tMaxUT = str(tMax_splitString[2][1:-1])
	tMaxJD_values = (tMaxJD, tmaxJD_err)

	tE_line = microTable[1].find_all('td')
	tE = float(tE_line[2].string)
	tE_err = float(tE_line[4].string.split()[0])
	tE_values = (tE, tE_err)

	u0_line = microTable[2].find_all('td')
	u0 = float(u0_line[2].string)
	u0_err = float(u0_line[4].string)
	u0_values = (u0, u0_err)

	mag_values = getMag_MOA(soup)
	if mag_values is not None:
		mag = mag_values[0]
		mag_err = mag_values[1]
	
	assessment = soup.find(string="Current assessment:").next_element.string
	remarks = soup.find_all("table")[1].find("td").string	

	lCurvePlotURL = "https://it019909.massey.ac.nz/moa/alert2015/datab/plot-" + ID + ".png"
	values_MOA = {"name": nameURL, "tMax": tMaxJD_values[0], "tMax_err": tMaxJD_values[1], \
								   "tE": tE_values[0], "tE_err":, tE_values[1], \
								   "u0": u0_values[0], "u0_err": u0_values[1], \
								   "mag": mag_values[0], "mag_err": mag_values[1], \
								   "lCurve": lCurvePlotURL, "assessment": assessment, "remarks": remarks}
	return values_MOA

def printOGLEvalues(eventName):
	OGLE_values = getOGLEvalues(eventName)

	"""
	print "Tmax: %s" % getString(OGLE_values[1])
	print "tau: %s" % getString(OGLE_values[2])
	print "u0: %s" % getString(OGLE_values[3])
	print "Light curve plot: %s" % OGLE_values[4]
	print "Light curve plot zoomed: %s" % OGLE_values[5]
	"""

getOGLEvalues(eventName):
	if eventName == None:
		print "No event found for %s" % eventName
		return
	print "Event name: %s" % eventName	
	nameURL = eventName[5:].lower()
	#print nameURL
	eventURL = "http://ogle.astrouw.edu.pl/ogle4/ews/" + nameURL + ".html"
	request = requests.get(eventURL, verify=False)
	page = request.content
	soup = BeautifulSoup(page, 'lxml')

	paramTable = soup.find_all("table")[2]
	paramRows = paramTable.find_all('tr')

	TmaxColumns = paramRows[0].find_all('td')
	tauColumns = paramRows[1].find_all('td')
	u0Columns = paramRows[2].find_all('td')

	TmaxValues = getValues_OGLE(TmaxColumns)
	tauValues = getValues_OGLE(tauColumns)
	u0Values = getValues_OGLE(u0Columns)

	lCurvePlotURL = "http://ogle.astrouw.edu.pl/ogle4/ews/data/2015/" + nameURL + "/lcurve.gif"
	lCurvePlotZoomedURL = "http://ogle.astrouw.edu.pl/ogle4/ews/data/2015/" + nameURL + "/lcurve_s.gif"

	values_OGLE = {"URL": eventURL, "tMax": TmaxValues[0], "tMax_err": TmaxValues[1], \
							 		"tE": tauValues[0], "tE_err": tauValues[1], \
									"u0": u0Values[0], "u0_err": u0Values[1] \
									"lCurve": lCurvePlotURL, "lCurveZoomed": lCurvePlotZoomedURL}
	return values_OGLE

def getValues_OGLE(columns):
	val = float(columns[1].string.split()[0])
	valErr = float(columns[3].string.split()[0])
	return (val, valErr)

def getString(values):
	return str(values[0]) + " +/- " + str(values[1])

def MOAtoOGLE(eventName):
	#example eventName: "2015-BLG-462"
	#MOA-OGLE cross reference: https://it019909.massey.ac.nz/moa/alert2015/moa2ogle.txt	
	return getEventName(eventName, isMOAtoOGLE=True)

def OGLEtoMOA(eventName):
	#example eventName: "2015-BLG-1812"
	#MOA-OGLE cross reference: https://it019909.massey.ac.nz/moa/alert2015/moa2ogle.txt	
	return getEventName(eventName, isMOAtoOGLE=False)

def getEventName(eventName, isMOAtoOGLE=True):
	crossReferenceURL = "https://it019909.massey.ac.nz/moa/alert2015/moa2ogle.txt"
	crossReferenceRequest = requests.get(crossReferenceURL, verify=False)
	crossReference = crossReferenceRequest.content.splitlines()
	if isMOAtoOGLE:
		eventName_old = "MOA-" + eventName
	else: #OGLE to MOA
		eventName_old = "OGLE-" + eventName
	eventName_new = ""
	print "Original event: %s" % eventName_old
	for line in reversed(crossReference):
		if line[0] != "#":
			lineSplit = line.split()
			if lineSplit[0] == eventName_old:
				eventName_new = lineSplit[2]
				break
			if lineSplit[2] == eventName_old:
				eventName_new = lineSplit[0]
				break
	print "New event: %s" % eventName_new
	if eventName_new == "":
		return None
	else:
		if isMOAtoOGLE:
			eventName_final = eventName_new[5:]
		else: #OGLE to MOA
			eventName_final = eventName_new[4:]
		print "Final event: %s" % eventName_final
		return eventName_final

def getID(eventName):
	indexRequest = requests.get("https://it019909.massey.ac.nz/moa/alert2015/index.dat", verify=False)
	index = indexRequest.content.splitlines()
	for line in reversed(index):
		lineSplit = line.split()
		if lineSplit[0] == eventName:
			return lineSplit[1]
	return None

def getMag_MOA(eventPageSoup):
	#Each magnitude is word 0 of string in table 3, row i, column 1 (zero-based numbering),
	#where i ranges from 2 through len(rows)-1 (inclusive).
	#Each error is word 1 of the same string.
	magTable = eventPageSoup.find(id="lastphot")
	rows = magTable.find_all('tr')

	#Iterate backwards over magnitudes starting from the most recent,
	#skipping over ones with too large errors
	for i in xrange(len(rows)-1, 1, -1):
		magStringSplit = rows[i].find_all('td')[1].string.split()
		mag = float(magStringSplit[0])
		magErr = float(magStringSplit[2])
		#print("Current magnitude: " + str(mag))
		#print("Current magnitude error: " + str(magErr))
		#Check if error exceeds max error allowed, and break out of loop if not.
		if (magErr <= MAX_MAG_ERR):
			magErrTooLarge = False
			#print("Magnitude error is NOT too large")
			break
		else:
			magErrTooLarge = True
			#print("Current magnitude error is too large")
	#If magnitude error is still too large after loop ends (without a break),
	#magErrTooLarge will be True.

	#if no magnitude rows were found in table, magnitude list is null
	if len(rows) > 2:
		magValues = (mag, magErr, magErrTooLarge)
	else:
		magValues = None

	return magValues

if __name__ == "__main__":
	main()
