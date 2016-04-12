"""
TAPtableRecording.py
Purpose: Download Markus and update TAP Kepler Short Candidate List from the the robonet server, then compare to stored list of event triggers from webpageAcesss.py
Author: Shanen Cross
Date: 2016-03-18
"""
import os
import sys
import requests
import csv
from bs4 import BeautifulSoup
import logging

import loggerSetup
import updateCSV

# Set up logger
LOG_DIR = os.path.join(sys.path[0], "logs/TAPtableRecordingLog")
LOG_NAME = "TAPtableRecordingLog"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
logger = loggerSetup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT)

# local script imports
#from compareEventTables import compareEvents
#from dataCollectionAndOutput import collectEventData

FILENAME = "targetListComparison.txt"
TAP_TARGET_TABLE_URL = "http://robonet.lcogt.net/temp/tap1mlist_kepler_short.html"
TEST_TAP_TARGET_TABLE_FILEPATH = "/home/scross/Documents/Workspace/RoguePlanetMicrolensingProject/webpageAccess/testing/shortTargetTableComparison/TAPtest2.html"
onlineTAPevents = {}

# set up and create ouptut directory and filename for TAP target table
TAP_TARGET_TABLE_OUTPUT_FILENAME = "TAPtargetTable.csv"
TAP_TARGET_TABLE_OUTPUT_DIR = os.path.join(sys.path[0], "TAPtargetTable")
TAP_TARGET_TABLE_OUTPUT_FILEPATH = os.path.join(TAP_TARGET_TABLE_OUTPUT_DIR, TAP_TARGET_TABLE_OUTPUT_FILENAME)
if not os.path.exists(TAP_TARGET_TABLE_OUTPUT_DIR):
	os.makedirs(TAP_TARGET_TABLE_OUTPUT_DIR)

LOCAL_TEST_ONLY = False

def updateTable():

	#print "Updating table."
	# Load local HTML file as TAP Target webpage if testing the script. 
	# If running the script for real, access the online TAP target page.
	if LOCAL_TEST_ONLY:
		logger.info("Running test with local file for TAP target table...")
		logger.info("Opening local page %s..." % (TEST_TAP_TARGET_TABLE_FILEPATH))
		#print "This is a local test. Opening local page %s..." % (TEST_TAP_TARGET_TABLE_FILEPATH)
		with open(TEST_TAP_TARGET_TABLE_FILEPATH, 'r') as pageFile:
			logger.info("File opened.")
			targetListSoup = BeautifulSoup(pageFile, "lxml") 
	else:
		logger.info("This is not a local test. Opening online page %s..." % (TAP_TARGET_TABLE_URL))
		targetListSoup = BeautifulSoup(requests.get(TAP_TARGET_TABLE_URL, verify=False).content, "lxml")

	logger.debug("Page soup acquired:\n" + targetListSoup.prettify())

	# Navigate to the webpage's event table with Beautiful Soup
	events = targetListSoup.find("table").find_all("tr")[1:]
	global onlineTAPevents
	onlineTAPevents = {} #empty list in case it was filled previously

	# Collect data from webpage soup
	for event in events:
		#print "Working on line:\n" + event.prettify()

		eventLines = event.find_all("td")
		eventName_full = eventLines[0].string
		eventPriority = eventLines[7].string
		eventMag = eventLines[9].string
		event_tE = eventLines[15].string
		event_tE_err = eventLines[16].string
		eventExposureTime = eventLines[6].string

		# obtains both MOA and OGLE names if available with name-conversion function from collectEventData...
		# But this should be done during generation of the comparison table between my output and Markus's TAP output, I think. 
		"""
		surveyPrefix = eventName_full.split("-")[0]
		eventName = eventName_full[(len(surveyPrefix) + 1):]

		if surveyPrefix == "MOA":
			eventName_MOA = eventName
			eventName_OGLE = collectEventData.convertEventName(eventName, MOAtoOGLE=True)
		elif surveyPREFIX == "OGLE":
			eventName_MOA = collectEventData.convertEventname(eventName, MOAtoOGLE=False)
			eventName_OGLE = eventName
		else:
			logger.warning("Error: Unexpected TAP event name formatting. Name " + eventName_full + "does not have either MOA or OGLE prefix."
			eventName_MOA = None
			eventName_OGLE = None
		"""
		
		# Store data as a dictionary of dictionaries. The inner dictionaries are the "events", containing items for each piece of data about the events.
		# The outer dictionary uses event names as keys, each pointing to an event dictionary as a value.
		eventDict = {"name_TAP": eventName_full, "priority_TAP": eventPriority, "mag_TAP": eventMag, "tE_TAP": event_tE, "tE_err_TAP": event_tE_err, \
					 "exposureTime_TAP": eventExposureTime}
		onlineTAPevents[eventName_full] = eventDict
		logger.debug("Obtained event dictionary: %s" % (str(eventDict)))
	#print "Obtained online TAP table: %s" % (str(onlineTAPevents))

def printOnlineTable():
	TAPnameList = sorted(onlineTAPevents)
	for eventName in TAPnameList:
		eventDict = onlineTAPevents[eventName]
		for item in eventDict:
			print item + ": " + eventDict[item]
		print

def saveTable():
	# Column field names for table
	fieldnames = ["name_TAP", "priority_TAP", "mag_TAP", "tE_TAP", "tE_err_TAP", "exposureTime_TAP"]
	delimiter = ","
	logger.info("Update .csv file with events using updateCSV script...")
	updateCSV.update(TAP_TARGET_TABLE_OUTPUT_FILEPATH, onlineTAPevents, fieldnames=fieldnames, delimiter=delimiter)
	
	"""
	# if csv file does NOT yet exist, open it for writing, sort the online TAP events by name, and store each event dictionary
	# as a row in this sequence
	if not os.path.isfile(TAP_TARGET_TABLE_OUTPUT_FILEPATH):
		#print "File does not exist. Opening file for writing..."
		with open(TAP_TARGET_TABLE_OUTPUT_FILEPATH, "w") as f:
			#print "File opened for writing."
			writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
			writer.writeheader()
			onlineTAPname_list = sorted(onlineTAPevents)
			#print "Sorted online TAP events: " + str(onlineTAPname_list)
			for eventName in onlineTAPname_list:
				eventDict = onlineTAPevents[eventName]
				#print "Writing dict to file: " + str(eventDict)
				writer.writerow(eventDict)

	# if file does already exist, read the existing file, get the sorted combined list of names from both online and locally stored events,
	# then write to file, storing each event dictionary from this combined list as a row in sequence. 
	# Store the updated online event dictionary when its available, else keep the local dictionary.
	else: 
		#print "File already exists. Opening file for reading..."
		with open(TAP_TARGET_TABLE_OUTPUT_FILEPATH, "r") as f:
			#print "File opened for reading."
			reader = csv.DictReader(f, delimiter=delimiter)
			
			# get dictionary with names as keys and event dictionaries as values for locally stored events
			localTAPevents ={}
			for row in reader:
				eventName = row["name_TAP"]
				localTAPevents[eventName] = row		

			#print "Local TAP events: " + str(localTAPevents)
			#print "Online TAP events: " + str(onlineTAPevents)
			# get set-like objects containing event names from local and online dictionaries,
			# then combine their set and sort it into an ordered list
			onlineTAPname_set = onlineTAPevents.viewkeys()
			localTAPname_set = localTAPevents.viewkeys()
			combinedTAPname_list = sorted(onlineTAPname_set | localTAPname_set)
			#print "combined set: " + str(onlineTAPname_set | localTAPname_set)
			#print "combined TAP name list: " + str(combinedTAPname_list)

		#print "Opening file for writing..."
		with open(TAP_TARGET_TABLE_OUTPUT_FILEPATH, "w") as f:
			#print "File opened for writing."
			#print "combined TAP name list: " + str(combinedTAPname_list)
			writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
			writer.writeheader()

			# Get and write the event dictionary for each event from the combined list in sequence. 
			# If available, get the online event. Otherwise, get the locally stored event.
			for name in combinedTAPname_list:
				if name in onlineTAPname_set:
					eventDict = onlineTAPevents[name]
				elif name in localTAPname_set:
					eventDict = localTAPevents[name]
				else:
					print "Error: Somehow the name %s in the combined list %s is not in either the local (%s) or online (%s) name sets." % \
						  (name, combinedTAPname_list, localTAPname_set, onlineTAPname_set)
					eventDict = None
				#print "Writing event dictionary: " + str(eventDict)
				writer.writerow(eventDict)
		"""
def updateAndSaveTable():
	logger.info("------------------------------------------------------------------------------")
	updateTable()
	saveTable()
	logger.info("------------------------------------------------------------------------------")

def main():
	updateAndSaveTable()	
	"""
	updateTable()
	#printOnlineTable()
	#print "Online TAP events: " + str(onlineTAPevents)
	saveTable()
	"""

if __name__== "__main__":
	main()
