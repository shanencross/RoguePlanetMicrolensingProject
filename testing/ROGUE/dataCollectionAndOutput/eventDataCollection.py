"""
eventDataCollection.py
IN-PROGRESS WORKING COPY
Author: Shanen Cross
Date: 2016-03-21
Purpose: 
"""
import sys #for getting script directory
import os #for file-handling
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup #html parsing
import csv

import loggerSetup
import updateCSV

requests.packages.urllib3.disable_warnings()

#create and set up filepath and directory for logs -
#log dir is subdir of script
LOG_DIR = os.path.join(sys.path[0], "logs/eventDataCollectionLog")
LOG_NAME = "eventDataCollectionLog"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
logger = loggerSetup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT)

MAX_MAG_ERR = 0.7

#for accessing URLs; default value is current year, but buildPage() changes this to MOA event name year,
#in case it has been given an event from a year different year
CURRENT_YEAR = str(datetime.utcnow().year)
#CURRENT_YEAR = "2015" #JUST FOR TESTING/DEBUGGING - REMOVE
eventYear = CURRENT_YEAR

#MOA and OGLE directories set to current year by defaultr; 
#buildPage() changes these if passed event from different year
MOA_dir = "https://it019909.massey.ac.nz/moa/alert" + eventYear
OGLE_dir = "http://ogle.astrouw.edu.pl/ogle4/ews"
#OGLE_dir = "http://ogle.astrouw.edu.pl/ogle4/ews/2015" #JUST FOR TESTING/DEBUGGING - REMOVE AND REPLACE WITH ABOVE COMMENTED LINE

#comment this out when saving as in-use copy
"""
EVENT_FILENAME = "summaryPageTest.html"
EVENT_DIR = os.path.join(sys.path[0], "summaryPageOutputTests")
EVENT_FILEPATH = os.path.join(EVENT_DIR, EVENT_FILENAME)
if not os.path.exists(EVENT_DIR):
	os.makedirs(EVENT_DIR)
"""

ARTEMIS_DIR = "/science/robonet/rob/Operations/Signalmen_output/model"
SUMMARY_OUTPUT_DIR = "/home/scross/Documents/Workspace/RoguePlanetMicrolensingProject/webpageAccess/testing/eventSummaryPages"
#change SUMMARY_OUTPUT_DIR to the following when saving as in-use copy.

#NOTE: Temporarily, output hardcoded to 2015 robonet log directory with TEMP_YEAR. Outputting to 2016 folder results 
#in dead links #to summaries in email alerts. Only 2015 folder uploads to current URLs. Is the 2016 folder uploading to somewhere
#else on the server?

#NOTE 2: TEMP_YEAR isn't working anymore, so perhaps they updated things? No files from the 2015 folder are on the 
#server anymore, only those in the 2016 folder. Now using CURRENT_YEAR instead.
#TEMP_YEAR = "2015"
#SUMMARY_OUTPUT_DIR = "/science/robonet/rob/Operations/Logs/" + CURRENT_YEAR + "/WWWLogs/eventSummaryPages"


EVENT_TRIGGER_RECORD_DIR = "/home/scross/Documents/Workspace/RoguePlanetMicrolensingProject/webpageAccess/testing/eventTriggerRecord"
# change EVENT_TRIGGER_RECORD_DIR to the following when saving as in-use copy:
# EVENT_TRIGGER_RECORD_DIR = os.path.join(sys.path[0], "eventTriggerRecord")
EVENT_TRIGGER_RECORD_FILENAME = "eventTriggerRecord.csv"
EVENT_TRIGGER_RECORD_FILEPATH = os.path.join(EVENT_TRIGGER_RECORD_DIR, EVENT_TRIGGER_RECORD_FILENAME)
if not os.path.exists(EVENT_TRIGGER_RECORD_DIR):
	os.makedirs(EVENT_TRIGGER_RECORD_DIR)

#values_MOA keywords: name, pageURL, tMax, tMax_err, tE, tE_err, u0, u0_err, mag, mag_err, assessment, lCurve, remarks, RA, Dec
#values_OGLE keywords: name, pageURL, tMax, tMax_err, tE, tE_err, u0, u0_err, lCurve, lCurveZoomed, remarks
def collectData(eventPageSoup, values_MOA, simulate=True):
	logger.info("--------------------------------------------")

	#set year to that of MOA event, for accessing URLs, and update MOA/OGLE URl directories
	updateYear(values_MOA["name"].split("-")[0])

	#update the current MOA values with the remaining ones that still need to be pulled from the webpage 
	#(the errors, remarks, and lightcurve URL)
	remainingValues_MOA = getRemainingValues_MOA(eventPageSoup, values_MOA["ID"])
	values_MOA.update(remainingValues_MOA)
	logger.debug("MOA values: " + str(values_MOA))
	name_OGLE = convertEventName(values_MOA["name"], MOAtoOGLE=True)
	if name_OGLE is not None:
		values_OGLE = getValues_OGLE(name_OGLE)
		values_ARTEMIS_OGLE = getValues_ARTEMIS(name_OGLE, isMOA=False)
	else:
		values_OGLE = None
		values_ARTEMIS_OGLE = None
	values_ARTEMIS_MOA = getValues_ARTEMIS(values_MOA["name"], isMOA=True)

	output_dict = {}
	if values_MOA is not None:
		output_dict["MOA"] = values_MOA
	if values_OGLE is not None:
		output_dict["OGLE"] = values_OGLE
	if values_ARTEMIS_MOA is not None:
		output_dict["ARTEMIS_MOA"] = values_ARTEMIS_MOA
	if values_ARTEMIS_OGLE is not None:
		output_dict["ARTEMIS_OGLE"] = values_ARTEMIS_OGLE

	return output_dict

def buildSummary(values_dict):
	outputString = buildOutputString(values_dict)
	logger.info("Output:\n" + outputString)
	
	if not os.path.exists(SUMMARY_OUTPUT_DIR):
		os.makedirs(SUMMARY_OUTPUT_DIR)
	outputFilename = values_dict["MOA"]["name"] + "_summary.html"
	outputFilepath = os.path.join(SUMMARY_OUTPUT_DIR, outputFilename)
	with open(outputFilepath, 'w') as outputFile:
		outputFile.write(outputString)
	logger.info("--------------------------------------------")

"""
def outputTable(input_dict):
	logger.info("Outputting table...")
	new_dict = {}
	
	#name_MOA, pageURL_MOA, tMax_MOA, tMax_err_MOA, tE_MOA, tE_err_MOA, u0_MOA, u0_err_MOA, mag_MOA, mag_err_MOA, assessment, lCurve_MOA, remarks_MOA
	#name_OGLE, pageURL_OGLE, tMax_OGLE, tMax_err_OGLE, tE_OGLE, tE_err_OGLE, u0_OGLE, u0_err_OGLE, mag_OGLE, mag_err_OGLE, lCurve_OGLE, lCurveZoomed_OGLE, remarks_OGLE
	#name_ARTEMIS_MOA, tMax_ARTEMIS_MOA, tMax_err_ARTEMIS_MOA, tE_ARTEMIS_MOA, tE_err_ARTEMIS_MOA, u0_ARTEMIS_MOA, u0_err_ARTEMIS_MOA
	#name_ARTEMIS_OGLE, tMax_ARTEMIS_OGLE, tMax_err_ARTEMIS_OGLE, tE_ARTEMIS_OGLE, tE_err_ARTEMIS_OGLE, u0_ARTEMIS_OGLE, u0_err_ARTEMIS_OGLE


	fieldnames = ["name_MOA", "name_OGLE", "ID_MOA", "RA_MOA", "Dec_MOA", "tE_MOA", "tE_err_MOA", "tE_OGLE", "tE_err_OGLE", "tE_ARTEMIS_MOA", "tE_err_ARTEMIS_MOA", \
				  "tE_ARTEMIS_OGLE", "tE_err_ARTEMIS_OGLE", "u0_MOA", "u0_err_MOA", "u0_OGLE", "u0_err_OGLE", "u0_ARTEMIS_MOA", "u0_err_ARTEMIS_MOA", \
				  "u0_ARTEMIS_OGLE", "u0_err_ARTEMIS_OGLE", "mag_MOA", "mag_err_MOA"]
	delimiter = ","

	for fieldname in fieldnames:
		if fieldname[-12:] == "_ARTEMIS_MOA" and input_dict.has_key("ARTEMIS_MOA"):
			new_dict[fieldname] = input_dict["ARTEMIS_MOA"][fieldname[:-12]]

		elif fieldname[-4:] == "_MOA" and input_dict.has_key("MOA"):
			new_dict[fieldname] = input_dict["MOA"][fieldname[:-4]]

		elif fieldname[-13:] == "_ARTEMIS_OGLE" and input_dict.has_key("ARTEMIS_OGLE"):
			new_dict[fieldname] = input_dict["ARTEMIS_OGLE"][fieldname[:-13]]

		elif fieldname[-5:] == "_OGLE" and input_dict.has_key("OGLE"):
			new_dict[fieldname] = input_dict["OGLE"][fieldname[:-5]]

	logger.info("New dictionary: " + str(new_dict))

	updateCSV.update(EVENT_TRIGGER_RECORD_FILEPATH, new_dict, fieldnames=fieldnames, delimiter=delimiter)

	if os.path.isfile(EVENT_TRIGGER_RECORD_FILEPATH):
		with open(EVENT_TRIGGER_RECORD_FILEPATH, "a") as f:
			writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
			writer.writerow(new_dict)
	else:
		with open(EVENT_TRIGGER_RECORD_FILEPATH, "w") as f:
			writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
			writer.writeheader()
			writer.writerow(new_dict)
"""

#Update year and associated global URLs
def updateYear(newYear):
	global eventYear
	eventYear = newYear

	global MOA_dir
	MOA_dir = "https://it019909.massey.ac.nz/moa/alert" + eventYear

	#OGLE dir remains unchanged unless event year differs rom the current year
	if eventYear != CURRENT_YEAR:
		global OGLE_dir
		OGLE_dir = "http://ogle.astrouw.edu.pl/ogle4/ews/" + eventYear

#currently return dict of tMax err, tE err, u0 err, remarks, and lCurve URL, given soup and ID --
#Perhaps later, should be updated to return dict of all missing entries,
#given a partially full MOA values dict?
def getRemainingValues_MOA(eventPageSoup, ID):
	microTable = eventPageSoup.find(id="micro").find_all('tr')
	tMaxJD_err = float(microTable[0].find_all('td')[4].string.split()[0])
	tE_err = float(microTable[1].find_all('td')[4].string.split()[0])
	u0_err = float(microTable[2].find_all('td')[4].string)
	remarks = str(eventPageSoup.find_all("table")[1].find("td").string)
	lCurvePlotURL = MOA_dir + "/datab/plot-" + ID + ".png"
	updateValues = {"tMax_err": tMaxJD_err, "tE_err": tE_err, "u0_err": u0_err, "lCurve": lCurvePlotURL, "remarks": remarks}
	logger.debug("Updated values: " + str(updateValues))
	return updateValues

def convertEventName(eventName, MOAtoOGLE=True):
	crossReferenceURL = MOA_dir + "/moa2ogle.txt"
	crossReferenceRequest = requests.get(crossReferenceURL, verify=False)
	crossReference = crossReferenceRequest.content.splitlines()
	if MOAtoOGLE:
		initialSurvey = "MOA"
		finalSurvey = "OGLE"
	else:
		initialSurvey = "OGLE"
		finalSurvey = "MOA"

	eventName_initial = initialSurvey + "-" + eventName
	eventName_final = ""
	for line in reversed(crossReference):
		if line[0] != "#":
			lineSplit = line.split()
			if lineSplit[0] == eventName_initial:
				eventName_final = lineSplit[2]
				break
			if lineSplit[2] == eventName_initial:
				eventName_final = lineSplit[0]
				break
	if eventName_final == "":
		return None
	else:
		eventName_output = eventName_final[(len(finalSurvey) + 1):]
		logger.debug(initialSurvey + " to " + finalSurvey + " converted name: " + str(eventName_final))
		return eventName_output

def getValues_OGLE(eventName):
	nameURL = eventName[5:].lower()
	eventURL = OGLE_dir + "/" + nameURL + ".html"
	request = requests.get(eventURL, verify=False)
	page = request.content
	soup = BeautifulSoup(page, 'lxml')
	tables = soup.find_all("table")
	logger.debug(str(soup))
	introTable = tables[1]
	remarks = str(introTable.find_all('tr')[4].find_all("td")[1].string)
	#remarks = str(soup.find(string="Remarks       ").next_element.string)

	if remarks == "\n":
		remarks = "None"

	paramTable = tables[2]
	paramRows = paramTable.find_all('tr')

	TmaxColumns = paramRows[0].find_all('td')
	tauColumns = paramRows[1].find_all('td')
	u0Columns = paramRows[2].find_all('td')

	TmaxValues = parseValues_OGLE(TmaxColumns)
	tauValues = parseValues_OGLE(tauColumns)
	u0Values = parseValues_OGLE(u0Columns)

	lCurvePlotURL = OGLE_dir + "/data/" + eventYear + "/" + nameURL + "/lcurve.gif"
	lCurvePlotZoomedURL = OGLE_dir + "/data/" + eventYear + "/" + nameURL + "/lcurve_s.gif"

	values = {"name": eventName, "pageURL": eventURL, "remarks": remarks, \
								 "tMax": TmaxValues[0], "tMax_err": TmaxValues[1], \
								 "tE": tauValues[0], "tE_err": tauValues[1], \
								 "u0": u0Values[0], "u0_err": u0Values[1], \
								 "lCurve": lCurvePlotURL, "lCurveZoomed": lCurvePlotZoomedURL}

	logger.debug("OGLE values: " + str(values))
	return values

def parseValues_OGLE(columns):
	val = float(columns[1].string.split()[0])
	valErr = float(columns[3].string.split()[0])
	return (val, valErr)

def getValues_MOA(ID):
	nameURL = MOA_dir + "/display.php?id=" + ID
	request = requests.get(nameURL, verify=False)
	page = request.content
	soup = BeautifulSoup(page, 'lxml')
	eventName = str(soup.find("title").string.split()[1])
	microTable = soup.find(id="micro").find_all('tr')

	tMax_line = microTable[0].find_all('td')
	tMaxJD = float(tMax_line[2].string.split()[1])
	tMax_splitString = tMax_line[4].string.split()
	tMaxJD_err = float(tMax_splitString[0])
	tMaxUT = str(tMax_splitString[2][1:-1])
	tMaxJD_values = (tMaxJD, tMaxJD_err)

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
	remarks = str(soup.find_all("table")[1].find("td").string)

	lCurvePlotURL = MOA_dir + "/datab/plot-" + ID + ".png"
	values_MOA = {"name": eventName, "pageURL": nameURL, 
				  "tMax": tMaxJD_values[0], "tMax_err": tMaxJD_values[1], \
				  "tE": tE_values[0], "tE_err": tE_values[1], \
				  "u0": u0_values[0], "u0_err": u0_values[1], \
				  "mag": mag_values[0], "mag_err": mag_values[1], 
				  "lCurve": lCurvePlotURL, "assessment": assessment, "remarks": remarks}

	logger.info("MOA values: " + str(values_MOA))
	return values_MOA	

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

	logger.debug("Mag values: " + str(magValues))
	return magValues

def getValues_ARTEMIS(eventName, isMOA=True):
	if isMOA:
 		filename = "KB"
	else: #is OGLE
		filename = "OB"
	filename += eventName[2:4] + "%04d" % int(eventName[9:])
	modelFilepath = os.path.join(ARTEMIS_DIR, filename + ".model")
	if not os.path.isfile(modelFilepath):
		return None
	with open(modelFilepath,'r') as file:
		line = file.readline()
	entries = line.split()
	t0 = float(entries[3]) + 2450000.0 #UTC(?)
	t0_err = float(entries[4])
	tE = float(entries[5]) #days
	tE_err = float(entries[6])
	u0 = float(entries[7]) 
	u0_err = float(entries[8])
	values = {"name": filename, "tMax": t0, "tMax_err": t0_err, "u0": u0, "u0_err": u0_err, "tE": tE, "tE_err": tE_err}
	if isMOA:
		logger.info("ARTEMIS MOA values: " + str(values))
	else: # is OGLE
		logger.info("ARTEMIS OGLE values: " + str(values))
	return values

#values_MOA keywords: name, assessment, remarks, tMax, tMax_err, tE, tE_err, u0, u0_err, mag, mag_err, lCurve, RA, Dec
#values_OGLE keywords: name, remarks, tMax, tMax_err, tE, tE_err, u0, u0_err, lCurve, lCurveZoomed
#values_ARTEMIS_MOA: name, tMax, tE, u0
def buildOutputString(values_dict):
	if values_dict.has_key("MOA"):
		values_MOA = values_dict["MOA"]
	else:
		values_MOA = None

	if values_dict.has_key("OGLE"):
		values_OGLE = values_dict["OGLE"]
	else:
		values_OGLE = None

	if values_dict.has_key("ARTEMIS_MOA"):
		values_ARTEMIS_MOA = values_dict["ARTEMIS_MOA"]
	else:
		values_ARTEMIS_MOA = None

	if values_dict.has_key("ARTEMIS_OGLE"):
		values_ARTEMIS_OGLE = values_dict["ARTEMIS_OGLE"]
	else:
		values_ARTEMIS_OGLE = None

	outputString = ""

	if values_MOA is not None:
		outputString += \
"""MOA event: <br>
Event: <a href=%s>%s</a> <br>
Assessment: %s <br>
Remarks: %s <br>
tMax: %s +/- %s <br>
tE: %s +/- %s <br>
u0: %s +/- %s <br>
Most recent magnitude: %s +/- %s <br>
Light Curve: <br>
<img src=%s width=500> \
""" % (values_MOA["pageURL"], values_MOA["name"], values_MOA["assessment"], values_MOA["remarks"], values_MOA["tMax"], values_MOA["tMax_err"], \
		values_MOA["tE"], values_MOA["tE_err"], values_MOA["u0"], values_MOA["u0_err"], values_MOA["mag"], values_MOA["mag_err"], \
		values_MOA["lCurve"])

	if values_OGLE is not None:
		outputString += \
"""\
<br>
<br>
OGLE event: <br> 
Event: <a href=%s>%s</a> <br>
Remarks: %s <br>
tMax: %s +/- %s <br>
tE: %s +/- %s <br>
u0: %s +/- %s <br>
Light Curve: <br>
<img src="%s" height=512 width=600> <br>
Light Curve Zoomed: <br>
<img src="%s" height=512 width=600> \
""" % (values_OGLE["pageURL"], values_OGLE["name"], values_OGLE["remarks"], values_OGLE["tMax"], values_OGLE["tMax_err"], \
		values_OGLE["tE"], values_OGLE["tE_err"], values_OGLE["u0"], values_OGLE["u0_err"], \
		values_OGLE["lCurve"], values_OGLE["lCurveZoomed"])

	if values_ARTEMIS_MOA is not None:
		outputString += \
"""\
<br>
<br>
ARTEMIS values using MOA event: <br>
Event: %s <br>
tMax: %s +/- %s <br>
tE: %s +/- %s <br>
u0: %s +/-%s\
""" % (values_ARTEMIS_MOA["name"], values_ARTEMIS_MOA["tMax"], values_ARTEMIS_MOA["tMax_err"], \
									values_ARTEMIS_MOA["tE"], values_ARTEMIS_MOA["tE_err"], \
									values_ARTEMIS_MOA["u0"], values_ARTEMIS_MOA["u0_err"])

	if values_ARTEMIS_OGLE is not None:
		outputString += \
"""\
<br>
<br>
ARTEMIS values using OGLE event: <br>
Event: %s <br>
tMax: %s +/- %s <br>
tE: %s +/- %s <br>
u0: %s +/-%s\
""" % (values_ARTEMIS_OGLE["name"], values_ARTEMIS_OGLE["tMax"], values_ARTEMIS_OGLE["tMax_err"], \
									values_ARTEMIS_OGLE["tE"], values_ARTEMIS_OGLE["tE_err"], \
									values_ARTEMIS_OGLE["u0"], values_ARTEMIS_OGLE["u0_err"])


#For testing observation trigger button functionality
#	outputString += \
#"""\
#<br>
#<br>
#<form action=http://robonet.lcogt.net/cgi-bin/private/cgiwrap/robouser/buttonTesting.py>
#<input type = "submit" value = "submit" />
#</form>\
#"""

	return outputString

def get_sexigesimal_RA_and_Dec(soup):
	RA = soup.find(string="RA:").next_element.string
	Dec = soup.find(string="Dec:").next_element.string
	return {"RA": RA, "Dec": Dec}

def test1():
	#MOA 2015-BLG-501
	#testID = "gb4-R-8-58133"
	#updateYear("2015")
	#testID = "gb14-R-2-53554"	
	testID = "gb19-R-7-5172"
	values_MOA = getValues_MOA(testID)
	name_OGLE = convertEventName(values_MOA["name"], MOAtoOGLE=True)
	values_OGLE = getValues_OGLE(name_OGLE)
	values_ARTEMIS_MOA = getValues_ARTEMIS(values_MOA["name"], isMOA=True)
	values_ARTEMIS_OGLE = getValues_ARTEMIS(name_OGLE, isMOA=False)
	outputString = buildOutputString(values_MOA, values_OGLE, values_ARTEMIS_MOA, values_ARTEMIS_OGLE)

	"""
	outputString += "MOA: <br>\n"
	for key in values_MOA.iterkeys():
		outputString += str(key) + ": " + str(values_MOA[key])
		outputString += "<br>\n"
	outputString += "<br>\n"
	outputString += "OGLE: <br>\n"
	for key in values_OGLE.iterkeys():
		outputString += str(key) + ": " + str(values_OGLE[key])
		outputString += "<br>\n"
	"""

	print outputString
	with open(EVENT_FILEPATH, 'w') as outputTest:
		outputTest.write(outputString)

def test2():
	testID = "gb19-R-7-5172"
	updateYear("2016")

	values_MOA = getValues_MOA(testID)
	values_MOA.update({"RA":str(274.573436176), "Dec":str(-25.739123955)})
	name_OGLE = convertEventName(values_MOA["name"], MOAtoOGLE=True)
	values_OGLE = getValues_OGLE(name_OGLE)
	values_ARTEMIS_MOA = getValues_ARTEMIS(values_MOA["name"], isMOA=True)
	values_ARTEMIS_OGLE = getValues_ARTEMIS(name_OGLE, isMOA=False)

	output_dict = {}
	if values_MOA is not None:
		output_dict["MOA"] = values_MOA
	if values_OGLE is not None:
		output_dict["OGLE"] = values_OGLE
	if values_ARTEMIS_MOA is not None:
		output_dict["ARTEMIS_MOA"] = values_ARTEMIS_MOA
	if values_ARTEMIS_OGLE is not None:
		output_dict["ARTEMIS_OGLE"] = values_ARTEMIS_OGLE

	outputTable(output_dict)

def main():
	test2()

if __name__ == "__main__":
	main()
