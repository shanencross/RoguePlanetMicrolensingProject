"""
webpageAccess.py
IN-PROGRESS WORKING COPY
Purpose: Poll MOA (and eventually OGLE) website for microlensing events, checking for ones likely to 
indicate rogue planets or planets distant from their parent star
Author: Shanen Cross
Date: 2016-03-18
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
from dataCollectionAndOutput import collectEventData # collecting data from survey sites and ARTEMIS, as well as outputting HTML summary page and event trigger record .csv
import mailAlert # script for sending emails by executing command line tool

requests.packages.urllib3.disable_warnings() # to disable warnings when accessing insecure sites

# create and set up filepath and directory for logs -
# log dir is subdir of script
LOG_DIR = os.path.join(sys.path[0], "logs")
LOG_NAME = "webpageAccessLog"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
logger = loggerSetup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT)

# set up filepath and directory for local copy of newest microlensing event
EVENT_FILENAME = "lastEvent.txt"
EVENT_DIR = os.path.join(sys.path[0], "lastEvent")
EVENT_FILEPATH = os.path.join(EVENT_DIR, EVENT_FILENAME)
if not os.path.exists(EVENT_DIR):
	os.makedirs(EVENT_DIR)

# set year as constant using current date/time, for accessing URLs
CURRENT_YEAR = str(datetime.utcnow().year)

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

# Flag for mail alerts functionality and list of mailing addresses
MAIL_ALERTS_ON = False
SUMMARY_BUILDER_ON = True
EVENT_TRIGGER_RECORD_ON = True
MAILING_LIST = ["shanencross@gmail.com", "rstreet@lcogt.net"]

def main():
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
		with open(EVENT_FILEPATH, 'w') as eventFile:
			eventFile.write(newestEvent)

	else:
		# open event file for reading and writing
		with open(EVENT_FILEPATH, 'r') as eventFile:
			localEvent = eventFile.read()
		if newestEvent != localEvent:
			# check over new events, evaluating each for observation triggering
			checkEvents(localEvent, index)
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

def eventTrigger(eventPageSoup, values_MOA):
	"""Runs when an event fits our critera. Triggers mail alerts and builds summary if those flags are on."""
	logger.info("Event is potentially suitable for observation!")
	if MAIL_ALERTS_ON:
		logger.info("Mailing event alert...")
		sendMailAlert(values_MOA)
	if SUMMARY_BUILDER_ON or EVENT_TRIGGER_RECORD_ON:
		logger.info("Collecting further data from survey site(s) and ARTEMIS if available...")
		try:
			dataDict = collectEventData.collectData(eventPageSoup, values_MOA, simulate=True)
			if SUMMARY_BUILDER_ON:
				logger.info("Building and outputting event summary page...")
				collectEventData.buildSummary(dataDict)
			if EVENT_TRIGGER_RECORD_ON:
				logger.info("Outputting event to .csv record of event triggers...")
				collectEventData.outputTable(dataDict)
		except Exception as ex:
			logger.warning("Exception collecting data and building/outputting event summary and/or event trigger record")
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

if __name__ == "__main__":
	main()
