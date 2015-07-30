"""
webpageAccess.py
ACTIVE IN-USE COPY
Purpose: Poll MOA (and eventually OGLE) website for microlensing events, checking for ones likely to 
indicate rogue planets or planets distant from their parent star
Author: Shanen Cross
Date: 2015-07-29
"""

import sys #not needed, used for debugging (e.g. calling exit())
import os #for file-handling
import logging
import loggerSetup
import requests #for fetching webpages
requests.packages.urllib3.disable_warnings() #to disable warnings when accessing insecure sites
from bs4 import BeautifulSoup #html parsing
from astropy.time import Time #not used yet, may need eventually for manipulating dates
import mailAlert #for sending email alerts

#create and set up filepath and directory for logs -
#log dir is subdir of script
LOG_DIR = os.path.join(sys.path[0], "logs")
LOG_NAME = "webpageAccessLog"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
logger = loggerSetup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT)

#set up filepath and directory for local copy of newest microlensing event
EVENT_FILENAME = "lastEvent.txt"
EVENT_DIR = os.path.join(sys.path[0], "lastEvent")
EVENT_FILEPATH = os.path.join(EVENT_DIR, EVENT_FILENAME)
if not os.path.exists(EVENT_DIR):
	os.makedirs(EVENT_DIR)

#setup URL paths for website event index and individual pages
WEBSITE_URL = "https://it019909.massey.ac.nz/moa/alert2015/"
INDEX_URL_DIR= "/index.dat"
INDEX_URL = WEBSITE_URL + INDEX_URL_DIR
EVENT_PAGE_URL_DIR = "/display.php?id=" #event page URL path is this with id number attached to end

#column numbers for event ID, Einstein time and baseline magnitude
#for index.dat file (zero-based counting)
NAME_INDEX = 0
ID_INDEX = 1
TIME_INDEX = 5
BASELINE_MAG_INDEX = 7

MAX_EINSTEIN_TIME = 3 #days - only check events as short or shorter than this
MIN_MAG = 17.5 #magnitude units - only check events as bright or brighter than this 
			   #(i.e. numerically more negative values)
MAX_MAG_ERR = 0.7 #magnitude unites - maximum error allowed for a mag

#Flag for mail alerts functionality and list of mailing addresses
MAIL_ALERTS_ON = True
MAILING_LIST = [ 'shanencross@gmail.com', 'rstreet@lcogt.net' ]

def main():
	logger.info("---------------------------------------")
	logger.info("Starting program")
	logger.info("Storing newest event in: " + EVENT_FILEPATH)
	logger.info("Max Einstein Time allowed: " + str(MAX_EINSTEIN_TIME) + " days")
	logger.info("Dimmest magnitude allowed: " + str(MIN_MAG))
	logger.info("Max magnitude error allowed: " + str(MAX_MAG_ERR))

	#get index.dat text from website, which lists events
	indexRequest = requests.get(INDEX_URL, verify=False)
	index = indexRequest.content.splitlines()
	#latest server event, to be written to local file if necessary
	newestEvent = index[-1]

	#if file does not already exist,check and evaluate all events
	if not os.path.isfile(EVENT_FILEPATH):
		localEvent = ""
		checkEvents(localEvent, index)
		with open(EVENT_FILEPATH, 'w') as eventFile:
			eventFile.write(newestEvent)

	else:
		#open event file fir reading and writing
		with open(EVENT_FILEPATH, 'r') as eventFile:
			localEvent = eventFile.read()
		if newestEvent != localEvent:
			#check over new events, evaluating each for observation triggering
			checkEvents(localEvent, index)
			#overwrite old local event with newest event after reading if updated is needed
			with open(EVENT_FILEPATH, 'w') as eventFile:
				#eventFile.seek(0)
				eventFile.write(newestEvent)
				#eventFile.truncate()
		else:
			logger.info("No new or updated events. Local file is up to date.")
	logger.info("Ending program")
	logger.info("---------------------------------------")

#check over new events, evaluating each for observation triggering
def checkEvents(localEvent, index):
	localEventSplit = localEvent.split()
	newestEventSplit = index[-1].split()
	#check that event line has enough elements to have name listed
	if len(localEventSplit) > NAME_INDEX:
		localEventName = localEventSplit[NAME_INDEX]
	else:
		localEventName = ""
	newestEventName = newestEventSplit[NAME_INDEX]

	#iterate backwards from last server event over
	#preceding events
	currentEventName = newestEventSplit[NAME_INDEX];
	for currentEvent in reversed(index):
		currentEventSplit = currentEvent.split()
		currentEventName = currentEventSplit[NAME_INDEX]
		#stop looping if we reach a server event that matches the local event
		if currentEventName == localEventName:
			logger.info("")
			logger.info("Match found! Event: " + currentEventName)
			break
		#evaluate current event for observation triggering
		evaluateEvent(currentEventSplit)

#evaluate whether event is short enough to potentially indicate a rogue planet
#and whether it is bright enough to be worth further observation
def evaluateEvent(splitEvent):
	logger.info("")
	logger.info("Event Evaluation:")
	#print "Event to be evaluated:\n" + ' '.join(splitEvent)
	logger.info("Event Name: " + splitEvent[NAME_INDEX])
	logger.info("Event ID: " + splitEvent[ID_INDEX])
	#print "Einsten time: " + splitEvent[TIME_INDEX]
	#print "Baseline magnitude: " + splitEvent[BASELINE_MAG_INDEX]

	#evaluate Einstein time, microlensing vs. cv status, and magnitude
	#for whether to trigger observation
	if checkEinsteinTime(splitEvent):
		eventPageSoup = getEventPageSoup(splitEvent)
		if isMicrolensing(eventPageSoup):
			if checkMag(eventPageSoup):
				logger.info("Event is potentially suitable for observation!")
				if MAIL_ALERTS_ON:
					logger.info("Mailing event alert...")
					sendMailAlert(splitEvent)
			else:
				logger.info("Magnitude fail")
		else:
			logger.info("Not microlensing")
	else:
		logger.info("Einstein time fail")

#check if Einstein time is fall enough for observation
def checkEinsteinTime(splitEvent):
	einsteinTime = float(splitEvent[TIME_INDEX])
	logger.info("Einstein Time: " + str(einsteinTime))
	if einsteinTime <= MAX_EINSTEIN_TIME:
		return True
	else:
		return False

#get BeautifulSoup object representing HTML page for event page
def getEventPageSoup(splitEvent):
	eventPageURL = WEBSITE_URL + EVENT_PAGE_URL_DIR + splitEvent[ID_INDEX]
	eventPageRequest = request = requests.get(eventPageURL, verify=False)
	eventPage = eventPageRequest.content
	eventPageSoup = BeautifulSoup(eventPage, 'lxml')
	return eventPageSoup

#check if event is microlensing, cv, a combination of the two, or unknown
#Should this return true or false if event is "microlensing/cv" (currently returns true)?
def isMicrolensing(eventPageSoup):
	#Best way to access microlensing vs. cv assessment?
	microlensingOrCV = eventPageSoup.find(string="Current assessment:").next_element.string
	logger.info("Current assessment: " + microlensingOrCV)
	if microlensingOrCV == "microlensing" or microlensingOrCV == "microlensing/cv":
		return True
	else:
		return False

#return magnitude and error of last photometry measurement whose error is not too large -
#if all found values are too large, returns false boolean as well
def getMag(eventPageSoup):
	#Each magnitude is word 0 of string in table 3, row i, column 1 (zero-based numbering),
	#where i ranges from 2 through len(rows)-1 (inclusive).
	#Each error is word 1 of the same string.
	magTable = eventPageSoup.find_all("table")[3]
	rows = magTable.find_all('tr')
	#Iterate backwards over magnitudes starting from the most recent,
	#skipping over ones with too large errors
	for i in xrange(len(rows)-1, 1, -1):
		magStringSplit = rows[i].find_all('td')[1].string.split()
		mag = float(magStringSplit[0])
		magErr = float(magStringSplit[2])
		logger.debug("Current magnitude: " + str(mag))
		logger.debug("Current magnitude error: " + str(magErr))
		#Check if error exceeds max error allowed, and break out of loop if not.
		if (magErr <= MAX_MAG_ERR):
			magErrTooLarge = False
			logger.debug("Magnitude error is NOT too large")
			break
		else:
			magErrTooLarge = True
			logger.debug("Current magnitude error is too large")
	#If magnitude error is still too large after loop ends (without a break),
	#magErrTooLarge will be True.
	return [mag, magErr, magErrTooLarge]

#check if magnitude is bright enough for observation
def checkMag(eventPageSoup):
	#get magnitude, error, and whether error is too large
	magList = getMag(eventPageSoup)
	#logger.debug("Returned mag array: " + str(magList))
	mag = magList[0]
	magErr = magList[1]
	magErrTooLarge = magList[2]
	logger.info("Magnitude: " + str(mag))
	logger.info("Magnitude error: " + str(magErr))

	#more negative mags are brighter, so we want values less than
	#our minimum brightness magnitude	
	if mag > MIN_MAG or magErrTooLarge:
		return False
	else:
		return True

#Send mail alert upon detecting short duration microlensing event
def sendMailAlert(splitEvent):
	mailSubject = splitEvent[NAME_INDEX] + " - Short Duration Microlensing Event Alert"
	eventPageURL = WEBSITE_URL + EVENT_PAGE_URL_DIR + splitEvent[ID_INDEX]
	messageText = \
"""\
Short Duration Microlensing Event Alert
Event Name: %s
Event ID: %s
Einstein Time: %s
MOA Event Page: %s\
""" % (splitEvent[NAME_INDEX], splitEvent[ID_INDEX], splitEvent[TIME_INDEX], eventPageURL)
	mailAlert.send_alert(messageText, mailSubject, MAILING_LIST)

if __name__ == "__main__":
	main()
