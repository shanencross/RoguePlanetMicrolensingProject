"""
webpageAccesTesting.py
Purpose: Poll MOA (and eventually OGLE) website for microlensing events, checking for ones likely to 
indicate rogue planets or planets distant from their parent star
Author: Shanen Cross
Date: 2015-07-22
"""

import sys #not needed, used for debugging (e.g. calling exit())
import os #for file-handling
import logging
import loggerSetup
import requests #for fetching webpages
requests.packages.urllib3.disable_warnings() #to disable warnings when accessing insecure sites
from bs4 import BeautifulSoup #html parsing
from astropy.time import Time #not used yet, may need eventually for manipulating dates

#create and set up filepath and directory for logs
LOG_DIR = "./logs/"
LOG_NAME = "webpageAccessTestingLog"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d_%H:%M:%S"
logger = loggerSetup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT)

#set up filepath and directory for local copy of newest microlensing event
EVENT_FILENAME = "lastEvent.txt"
EVENT_DIR = "./lastEvent/"
EVENT_FILEPATH = os.path.join(EVENT_DIR, EVENT_FILENAME)
if not os.path.exists(EVENT_DIR):
	os.makedirs(EVENT_DIR)

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

#setup URL paths for website event index and individual pages
WEBSITE_URL = "https://it019909.massey.ac.nz/moa/alert2015/"
INDEX_URL_DIR= "/index.dat"
INDEX_URL = WEBSITE_URL + INDEX_URL_DIR
EVENT_PAGE_URL_DIR = "/display.php?id=" #event page URL path is this with id number attached to end

def main():
	logger.info("Storing newest event in: " + EVENT_FILEPATH)
	logger.info("Max Einstein Time allowed: " + str(MAX_EINSTEIN_TIME) + " days")
	logger.info("Dimmest magnitude allowed: " + str(MIN_MAG))
	logger.info("Max magintude error allowed: " + str(MAX_MAG_ERR))

	#get index.dat text from website, which lists events
	indexRequest = requests.get(INDEX_URL, verify=False)
	index = indexRequest.content.splitlines()
	#latest server event, to be written to local file if necessary
	newestEvent = index[-1]

	#if file does not already exist, write newest event to file
	if not os.path.isfile(EVENT_FILEPATH):
		with open(EVENT_FILEPATH, 'w') as eventFile:
			eventFile.write(newestEvent)
		evaluateEvent(newestEvent.split())

	else:
		#open event file fir reading and writing
		with open(EVENT_FILEPATH, 'r+') as eventFile:
			localEvent = eventFile.read()
			#overwrite old local event with newest event after reading if updated is needed
			if newestEvent != localEvent:
				eventFile.seek(0)
				eventFile.write(newestEvent)
				eventFile.truncate()
		if newestEvent != localEvent:
			#check over new events, evaluating each for observation triggering
			checkEvents(localEvent, index)
		else:
			logger.info("No new or updated events. Local file is up to date.")

#check over new events, evaluating each for observatoin triggering
def checkEvents(localEvent, index):
	localEventSplit = localEvent.split()
	newestEventSplit = index[-1].split()
	#check that event line has enough elements to have name listed
	if len(localEventSplit) > NAME_INDEX:
			localEventName = localEventSplit[NAME_INDEX]
			newestEventName = newestEventSplit[NAME_INDEX]

			#iterate backwards from last server event over
			#preceding events
			i = -1
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
				logger.info("Trigger observation! ...if not too old")
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

#check if magnitude is bright enough for observation
def checkMag(eventPageSoup):
	#Each magnitude is 0th word in table 3, row i, column 1 (zero-based numbering),
	#where i ranges from 2 through 6 (inclusive). Mag from row i=6 is most recent.
	magTable = eventPageSoup.find_all("table")[3]
	magFound = False
	for i in xrange(6, 1, -1):
		magStringSplit = magTable.find_all('tr')[i].find_all('td')[1].string.split()
		mag = float(magStringSplit[0])
		magErr = float(magStringSplit[2])
		logger.debug("Current magnitude: " + str(mag))
		logger.debug("Current magnitude error: " + str(magErr))
		if (magErr <= MAX_MAG_ERR):
			magErrTooLarge = False
			logger.debug("Magnitude error is NOT too large")
			break
		else:
			magErrTooLarge = True
			logger.debug("Current magnitude error is too large")
	
	logger.info("Magnitude: " + str(mag))
	logger.info("Magnitude error: " + str(magErr))

	#more negative mags are brighter, so we want values less than
	#our minimum brightness magnitude	
	if mag > MIN_MAG or magErrTooLarge:
		return False
	else:
		return True

if __name__ == "__main__":
	main()
