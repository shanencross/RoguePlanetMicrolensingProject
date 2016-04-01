"""
ROGUE.py
IN-PROGRESS WORKING COPY
Purpose: Poll MOA (and eventually OGLE) website for microlensing events, checking for ones likely to 
indicate rogue planets or planets distant from their parent star
Author: Shanen Cross
Date: 2016-03-31
"""
"""
Note: Does not currently account for corresponding MOA and OGLE events possibly having different years.
For instance, some 2016 MOA events have 2015 OGLE counterparts.
This script will detect no OGLE counterpart for such a MOA event.
It will also ignore any MOA event prior to the current year, regardless of whether its OGLE
counterpart are listed in the current year.
"""
import sys # for getting script directory
import os # for file-handling
import logging
import requests # for fetching webpages
from bs4 import BeautifulSoup # html parsing dates
from datetime import datetime # for getting current year for directories and URLs
from K2fov.c9 import inMicrolensRegion # K2 tool for checking if given RA and Dec coordinates are in K2 Campaign 9 microlensing region

# local script imports
import loggerSetup # setting up logger
from dataCollectionAndOutput import eventDataCollection # collecting data from survey sites and ARTEMIS, as well as outputting HTML summary page and event trigger record .csv
import updateCSV
import eventTablesComparison
import mailAlert # script for sending emails by executing command line tool

requests.packages.urllib3.disable_warnings() # to disable warnings when accessing insecure sites

# create and set up filepath and directory for logs -
# log dir is subdir of script
LOG_DIR = os.path.join(sys.path[0], "logs/ROGUElog")
LOG_NAME = "ROGUElog"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
logger = loggerSetup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT)

# set up filepath and directory for local copy of newest microlensing event
EVENT_FILENAME = "lastEvent.txt"
EVENT_DIR = os.path.join(sys.path[0], "lastEvent")
EVENT_FILEPATH = os.path.join(EVENT_DIR, EVENT_FILENAME)
if not os.path.exists(EVENT_DIR):
	os.makedirs(EVENT_DIR)

# Set up filepath for .csv file of TAP event triggers
TAP_DIR = os.path.join(sys.path[0], "TAPtargetTable")
TAP_FILENAME = "TAPtargetTable.csv"
TAP_FILEPATH = os.path.join(TAP_DIR, TAP_FILENAME)

# Set up filepath for ROGUE vs. TAP comparison table HTML file
COMPARISON_TABLE_DIR = os.path.join(sys.path[0], "comparisonTable")
COMPARISON_TABLE_FILENAME = "ROGUE_vs_TAP_Comparison_Table.html"
COMPARISON_TABLE_FILEPATH = os.path.join(COMPARISON_TABLE_DIR, COMPARISON_TABLE_FILENAME)
if not os.path.exists(COMPARISON_TABLE_DIR):
	os.makedirs(COMPARISON_TABLE_DIR)

# set year as constant using current date/time, for accessing URLs
CURRENT_YEAR = str(datetime.utcnow().year)
#CURRENT_YEAR = "2015" #TEMPORARY FOR TESTING/DEBUGGING - CHANGE TO ABOVE LINE

# setup URL paths for website event index and individual pages
WEBSITE_URL = "https://it019909.massey.ac.nz/moa/alert" + CURRENT_YEAR + "/"
INDEX_URL_DIR= "/index.dat"
INDEX_URL = WEBSITE_URL + INDEX_URL_DIR
EVENT_PAGE_URL_DIR = "/display.php?id=" #event page URL path is this with id number attached to end

# column numbers for event ID, Einstein time and baseline magnitude
# for index.dat file (zero-based counting)
NAME_INDEX = 0
ID_INDEX = 1
RA_INDEX = 2
DEC_INDEX = 3
TMAX_INDEX = 4
TIME_INDEX = 5
U0_INDEX = 6
BASELINE_MAG_INDEX = 7

MAX_EINSTEIN_TIME = 3 # days - only check events as short or shorter than this
MIN_MAG = 17.5 # magnitude units - only check events as bright or brighter than this
			   # (i.e. numerically more negative values)
MAX_MAG_ERR = 0.7 # magnitude unites - maximum error allowed for a mag

EVENT_TRIGGER_RECORD_DIR = os.path.join(sys.path[0], "eventTriggerRecord")
EVENT_TRIGGER_RECORD_FILENAME = "eventTriggerRecord.csv"
EVENT_TRIGGER_RECORD_FILEPATH = os.path.join(EVENT_TRIGGER_RECORD_DIR, EVENT_TRIGGER_RECORD_FILENAME)
if not os.path.exists(EVENT_TRIGGER_RECORD_DIR):
	os.makedirs(EVENT_TRIGGER_RECORD_DIR)

# Fieldnames and delimiter for .csv file storing event triggers
FIELDNAMES = ["name_MOA", "name_OGLE", "ID_MOA", "RA_MOA", "Dec_MOA", "tE_MOA", "tE_err_MOA", "tE_OGLE", "tE_err_OGLE", "tE_ARTEMIS_MOA", "tE_err_ARTEMIS_MOA", \
			  "tE_ARTEMIS_OGLE", "tE_err_ARTEMIS_OGLE", "u0_MOA", "u0_err_MOA", "u0_OGLE", "u0_err_OGLE", "u0_ARTEMIS_MOA", "u0_err_ARTEMIS_MOA", \
			  "u0_ARTEMIS_OGLE", "u0_err_ARTEMIS_OGLE", "mag_MOA", "mag_err_MOA"]

DELIMITER = ","

# Flag for mail alerts functionality and list of mailing addresses
MAIL_ALERTS_ON = False
SUMMARY_BUILDER_ON = True
EVENT_TRIGGER_RECORD_ON = True
EVENT_TABLE_COMPARISON_ON = True
MAILING_LIST = ["shanencross@gmail.com", "rstreet@lcogt.net"]

# Golbal dictionary of event triggers to update .csv file with
eventTriggerDict = {}

def runROGUE():
	logger.info("---------------------------------------")
	logger.info("Starting program")
	logger.info("Storing newest event in: " + EVENT_FILEPATH)
	logger.info("Max Einstein Time allowed: " + str(MAX_EINSTEIN_TIME) + " days")
	logger.info("Dimmest magnitude allowed: " + str(MIN_MAG))
	logger.info("Max magnitude error allowed: " + str(MAX_MAG_ERR))

	# get index.dat text from website, which lists events
	indexRequest = requests.get(INDEX_URL, verify=False)
	index = indexRequest.content.splitlines()
	# latest server event, to be written to local file if necessary
	newestEvent = index[-1]

	# if file does not already exist,check and evaluate all events
	if not os.path.isfile(EVENT_FILEPATH):
		localEvent = ""
		checkEvents(localEvent, index)
		saveAndCompareTriggers()
		with open(EVENT_FILEPATH, 'w') as eventFile:
			eventFile.write(newestEvent)

	else:
		# open event file for reading and writing
		with open(EVENT_FILEPATH, 'r') as eventFile:
			localEvent = eventFile.read()
		if newestEvent != localEvent:
			# check over new events, evaluating each for observation triggering
			checkEvents(localEvent, index)
			saveAndCompareTriggers()
			# overwrite old local event with newest event after reading if updated is needed
			with open(EVENT_FILEPATH, 'w') as eventFile:
				# eventFile.seek(0)
				eventFile.write(newestEvent)
				# eventFile.truncate()
		else:
			logger.info("No new or updated events. Local file is up to date.")
	logger.info("Ending program")
	logger.info("---------------------------------------")

def checkEvents(localEvent, index):
	"""Check new events, evaluating each for observation triggering."""
	localEventSplit = localEvent.split()
	newestEventSplit = index[-1].split()
	# check that event line has enough elements to have name listed
	if len(localEventSplit) > NAME_INDEX:
		localEventName = localEventSplit[NAME_INDEX]
	else:
		localEventName = ""
	newestEventName = newestEventSplit[NAME_INDEX]

	# iterate backwards from last server event over
	# preceding events
	currentEventName = newestEventSplit[NAME_INDEX];
	for currentEvent in reversed(index):
		currentEventSplit = currentEvent.split()
		currentEventName = currentEventSplit[NAME_INDEX]
		# stop looping if we reach a server event that matches the local event
		if currentEventName == localEventName:
			logger.info("")
			logger.info("Match found! Event: " + currentEventName)
			break
		# evaluate current event for observation triggering
		evaluateEvent(currentEventSplit)

def evaluateEvent(splitEvent):
	"""Evaluate whether event is short enough to potentially indicate a rogue planet
	and whether it is bright enough to be worth further observation.
	"""
	logger.info("")
	logger.info("Event Evaluation:")

	# place relevant values from event row in MOA table into dictionary as strings for ease of access
	values_MOA = {"name": splitEvent[NAME_INDEX], "ID": splitEvent[ID_INDEX], "RA": splitEvent[RA_INDEX], \
				  "Dec": splitEvent[DEC_INDEX], "tMax": splitEvent[TMAX_INDEX], "tE": splitEvent[TIME_INDEX], \
				  "u0": splitEvent[U0_INDEX]}

	logger.info("Event Name: " + values_MOA["name"])
	logger.info("Event ID: " + values_MOA["ID"])

	# evaluate Einstein time, microlensing vs. cv status, and magnitude
	# for whether to trigger observation
	if checkEinsteinTime(values_MOA["tE"]):
		if checkMicrolensRegion(values_MOA["RA"], values_MOA["Dec"]):
			evaluateEventPage_MOA(values_MOA)
		else:
			logger.info("Microlensing region failed: Not in K2 Campaign 9 microlensing region")
	# fail to trigger if Einstein time is unacceptable
	else:
		logger.info("Einstein time failed: must be equal to or greater than " + str(MAX_EINSTEIN_TIME) + " days")

def eventTrigger(eventPageSoup, values_MOA):
	"""Runs when an event fits our critera. Triggers mail alerts and builds summary if those flags are on."""

	logger.info("Event is potentially suitable for observation!")
	if MAIL_ALERTS_ON:
		logger.info("Mailing event alert...")
		try:
			sendMailAlert(values_MOA)
		except Exception as ex:
			logger.warning("Exception attempting to mail event alert")
			logger.warning(ex)

	if SUMMARY_BUILDER_ON or EVENT_TRIGGER_RECORD_ON:
		logger.info("Collecting further data from survey site(s) and ARTEMIS if available...")
		try:
			dataDict = eventDataCollection.collectData(eventPageSoup, values_MOA, simulate=True)
		except Exception as ex:
			logger.warning("Exception collecting data from survey site(s) and/or ARTEMIS")
			logger.warning(ex)
			return

		if SUMMARY_BUILDER_ON:
			logger.info("Building and outputting event summary page...")
			try:
				eventDataCollection.buildSummary(dataDict)
			except Exception as ex:
				logger.warning("Exception building/outputting event summary")
				logger.warning(ex)

		if EVENT_TRIGGER_RECORD_ON:
			logger.info("Saving event dictionary to dictionary of event dictionaries, to be outputted later..")
			try:
				addEventToTriggerDict(dataDict)
			except Exception as ex:
				logger.warning("Exception converting event data dictionary format and/or saving event to event trigger dictionary.")
				logger.warning(ex)

def checkEinsteinTime(tE_string):
	"""Check if Einstein time is short enough for observation."""
	einsteinTime = float(tE_string)
	logger.info("Einstein Time: " + str(einsteinTime) + " days")
	if einsteinTime <= MAX_EINSTEIN_TIME:
		return True
	else:
		return False

def checkMicrolensRegion(RA_string, Dec_string):
	"""Check if strings RA and Dec coordinates are within K2 Campaign 9 microlensing region (units: degrees)."""
	# Convert strings to floats and output to logger
	RA = float(RA_string)
	Dec = float(Dec_string)
	logger.info("RA: " + str(RA) + "      Dec: " + str(Dec) + "      (Units: Degrees)")

	# pass to K2fov.c9 module method (from the K2 tools) to get whether coordinates are in the region
	return inMicrolensRegion(RA, Dec)


def evaluateEventPage_MOA(values_MOA):
	"""Continue evaluating event using information from the MOA event page."""
	# access MOA event page and get soup of page for parsing more values
	eventPageURL = WEBSITE_URL + EVENT_PAGE_URL_DIR + values_MOA["ID"]
	values_MOA["pageURL"] = eventPageURL
	eventPageSoup = BeautifulSoup(requests.get(eventPageURL, verify=False).content, 'lxml')

	# Parse page soup for microlensing assessment of event
	assessment = getMicrolensingAssessment(eventPageSoup)
	values_MOA["assessment"] = assessment

	if isMicrolensing(assessment):
		# parse page soup for magnitude and error of most recent observation of event
		magValues = getMag(eventPageSoup)
		values_MOA["mag"] = magValues[0]
		values_MOA["mag_err"] = magValues[1]

		# trigger if magnitude matches critera along with the preceding checks
		if checkMag(magValues):
			eventTrigger(eventPageSoup, values_MOA)

		# fail to trigger if mag and/or mag error values are unacceptable
		else:
			logger.info("Magnitude failed: must be brighter than " + str(MIN_MAG) + " AND have error less than " + str(MAX_MAG_ERR))

	# fail to trigger of assessment is non-microlensing
	else:
		logger.info("Assessment failed: Not assessed as microlensing")

def getMicrolensingAssessment(eventPageSoup):
	"""Get assessment of whether an event is microlensing. Could be microlensing, cv, microlensing/cv, 
	or possibly something else.
	"""
	assessment = eventPageSoup.find(string="Current assessment:").next_element.string
	return assessment

def isMicrolensing(assessment):
	"""Check if event is microlensing, cv, a combination of the two, or unknown -
    Should this return true or false if event is "microlensing/cv" (currently returns true)?
	"""
	logger.info("Current assessment: " + assessment)
	if assessment == "microlensing" or assessment == "microlensing/cv":
		return True
	else:
		return False

def getMag(eventPageSoup):
	"""Return magnitude and error of last photometry measurement whose error is not too large -
	if all found values are too large, returns false boolean as well.
	"""
	# Each magnitude is word 0 of string in table 3, row i, column 1 (zero-based numbering),
	# where i ranges from 2 through len(rows)-1 (inclusive).
	# Each error is word 1 of the same string.
	magTable = eventPageSoup.find_all("table")[3]
	rows = magTable.find_all('tr')

	# Iterate backwards over magnitudes starting from the most recent,
	# skipping over ones with too large errors
	for i in xrange(len(rows)-1, 1, -1):
		magStringSplit = rows[i].find_all('td')[1].string.split()
		mag = float(magStringSplit[0])
		magErr = float(magStringSplit[2])
		logger.debug("Current magnitude: " + str(mag))
		logger.debug("Current magnitude error: " + str(magErr))
		# Check if error exceeds max error allowed, and break out of loop if not.
		if (magErr <= MAX_MAG_ERR):
			magErrTooLarge = False
			logger.debug("Magnitude error is NOT too large")
			break
		else:
			magErrTooLarge = True
			logger.debug("Current magnitude error is too large")
	# If magnitude error is still too large after loop ends (without a break),
	# magErrTooLarge will be True.

	# if no magnitude rows were found in table, magnitude list is null
	if len(rows) > 2:
		magValues = (mag, magErr, magErrTooLarge)
	else:
		magValues = None
	return magValues

def checkMag(magValues):
	"""Check if magnitude is bright enough for observation."""
	# logger.debug("Returned mag array: " + str(magValues))
	# if no magnitudes were found
	if magValues is None:
		logger.info("Magnitude: None found")
		return False
	mag = magValues[0]
	magErr = magValues[1]
	magErrTooLarge = magValues[2]
	logger.info("Magnitude: " + str(mag))
	logger.info("Magnitude error: " + str(magErr))

	# more negative mags are brighter, so we want values less than
	# our minimum brightness magnitude	
	if mag > MIN_MAG or magErrTooLarge:
		return False
	else:
		return True

def addEventToTriggerDict(eventDataDict):
	"""Add event data dictionary (dictionary containing separate dictionaries for data from each survey) \
	to dictionary of event triggers, first converting it to a single event dictionary containing items from all surveys."""

	event = convertDataDict(eventDataDict)

	# Use OGLE name for key pointing to event as value if availble.
	if event.has_key("name_OGLE") and event["name_OGLE"] != "":
		logger.info("Event has OGLE name")
		nameKey = "name_OGLE"

	# Otherwise, use the MOA name.
	elif event.has_key("name_MOA") and event["name_MOA"] != "":
		logger.info("Event has MOA name and no OGLE name")
		nameKey = "name_MOA"

	# If there is a neither a MOA nor OGLE name, something has gone wrong, and we abort storing the event.
	else:
		logger.warning("Event has neither OGLE nor MOA name item. Event:\n" + str(event))
		logger.warning("Aborting added event to event trigger dictionary...")
		return

	eventName = event[nameKey]
	eventTriggerDict[eventName] = event

def convertDataDict(eventDataDict):
	"""Convert event data dictionary (dictionary containing separate dictionaries for data from each survey) \
	for an event to proper format, combining data from all surveys into one dictionary."""

	"""
	EventDataDict is a dictionary of up to four event dictionaries for the same event.
	They contain MOA, OGLE, ARTEMIS_MOA, and ARTEMIS_OGLE values respectively.
	We convert this to a single dictionary with items from all surveys, and keys with survey suffixes attached
	to distinguish, for examle, tE_MOA from the tE_OGLE.
	"""
	convertedEventDict = {}

	for fieldname in FIELDNAMES:
		if fieldname[-12:] == "_ARTEMIS_MOA" and eventDataDict.has_key("ARTEMIS_MOA") and eventDataDict["ARTEMIS_MOA"] != "":
			convertedEventDict[fieldname] = eventDataDict["ARTEMIS_MOA"][fieldname[:-12]]

		elif fieldname[-4:] == "_MOA" and eventDataDict.has_key("MOA") and eventDataDict["MOA"] != "":
			convertedEventDict[fieldname] = eventDataDict["MOA"][fieldname[:-4]]

		elif fieldname[-13:] == "_ARTEMIS_OGLE" and eventDataDict.has_key("ARTEMIS_OGLE") and eventDataDict["ARTEMIS_OGLE"] != "":
			convertedEventDict[fieldname] = eventDataDict["ARTEMIS_OGLE"][fieldname[:-13]]

		elif fieldname[-5:] == "_OGLE" and eventDataDict.has_key("OGLE") and eventDataDict["OGLE"] != "":
			convertedEventDict[fieldname] = eventDataDict["OGLE"][fieldname[:-5]]

		# Convert the shortened names such as "2016-BLG-123" to the full names with survey prefixes,
		# like "MOA-2016-BLG-123" or "OGLE-2016"BLG-123";
		# Last condition Probably not necessary, but just in case
		if fieldname[:5] == "name_" and convertedEventDict.has_key(fieldname) and convertedEventDict[fieldname] != "":
				surveyName = fieldname[5:]
				convertedEventDict[fieldname] = surveyName + "-" + convertedEventDict[fieldname]

		logger.debug("Converted event dict: " + str(convertedEventDict))

	return convertedEventDict

def saveAndCompareTriggers():
	if EVENT_TRIGGER_RECORD_ON:
		logger.info("Outputting event to .csv record of event triggers...")
		try:
			updateCSV.update(EVENT_TRIGGER_RECORD_FILEPATH, eventTriggerDict, fieldnames=FIELDNAMES, delimiter=DELIMITER)
		except Exception as ex:
			logger.warning("Exception outputting .csv record of event triggers")
			logger.warning(ex)
			return

		if EVENT_TABLE_COMPARISON_ON:
			logger.info("Generating and outputting HTML page with comparison table of ROGUE and TAP event triggers...")
			try:
				eventTablesComparison.compareAndOutput(EVENT_TRIGGER_RECORD_FILEPATH, TAP_FILEPATH, COMPARISON_TABLE_FILEPATH)
			except Exception as ex:
				logger.warning("Exception generating/outputting comparison table HTML page")
				logger.warning(ex)		

def sendMailAlert(values_MOA):
	"""Send mail alert upon detecting short duration microlensing event"""
	eventName = values_MOA["name"]
	mailSubject = eventName + " - Short Duration Microlensing Event Alert"
	summaryPageURL = "http://robonet.lcogt.net/robonetonly/WWWLogs/eventSummaryPages/" + eventName + "_summary.html"
	messageText = \
"""\
Short Duration Microlensing Event Alert
Event Name: %s
Event ID: %s
Einstein Time (MOA): %s
MOA Event Page: %s
Event summary page: %s\
""" % (eventName, values_MOA["ID"], values_MOA["tE"], values_MOA["pageURL"], summaryPageURL)
	mailAlert.send_alert(messageText, mailSubject, MAILING_LIST)
	logger.info("Event alert mailed!")

def main():
	runROGUE()

if __name__ == "__main__":
	main()
