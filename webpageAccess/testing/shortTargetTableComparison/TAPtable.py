"""
TAPtable.py
Purpose: Download Markus and update TAP Kepler Short Candidate List from the the robonet server, then compare to stored list of event triggers from webpageAcesss.py
Author: Shanen Cross
Date: 2016-03-18
"""
import os
import sys
import requests
import csv
from bs4 import BeautifulSoup

# local script imports
from compareEventTables import compareEvents
#from dataCollectionAndOutput import collectEventData

FILENAME = "targetListComparison.txt"
TAP_TARGET_TABLE_URL = "http://robonet.lcogt.net/temp/tap1mlist_kepler_short.html"
TEST_TAP_TARGET_TABLE_FILEPATH = "/home/scross/Documents/Workspace/RoguePlanetMicrolensingProject/webpageAccess/testing/shortTargetTableComparison/TAPtest2.html"
onlineTAPevents = {}

# set up and create ouptut directory and filename for TAP target table
TAP_TARGET_TABLE_OUTPUT_FILENAME = "TAP_target_table.csv"
TAP_TARGET_TABLE_OUTPUT_DIR = os.path.join(sys.path[0], "TAPtargetTable")
TAP_TARGET_TABLE_OUTPUT_FILEPATH = os.path.join(TAP_TARGET_TABLE_OUTPUT_DIR, TAP_TARGET_TABLE_OUTPUT_FILENAME)
if not os.path.exists(TAP_TARGET_TABLE_OUTPUT_DIR):
	os.makedirs(TAP_TARGET_TABLE_OUTPUT_DIR)

LOCAL_TEST_ONLY = True

def updateTable():

	print "Updating table."
	# Load local HTML file as TAP Target webpage if testing the script. 
	# If running the script for real, access the online TAP target page.
	if LOCAL_TEST_ONLY:
		print "This is a local test. Opening local page %s..." % (TEST_TAP_TARGET_TABLE_FILEPATH)
		with open(TEST_TAP_TARGET_TABLE_FILEPATH, 'r') as pageFile:
			print "File opened."
			targetListSoup = BeautifulSoup(pageFile, "lxml") 
	else:
		print "This is not a local test. Opening online page %s..." % (TAP_TARGET_TABLE_URL)
		targetListSoup = BeautifulSoup(requests.get(TAP_TARGET_TABLE_URL, verify=False).content, "lxml")

	#print "Page soup acquired:\n" + targetListSoup.prettify()

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
		eventDict = {"name_TAP": eventName_full, "priority_TAP": eventPriority, "mag_TAP": eventMag, "tE_TAP": event_tE, "tE_err_TAP": event_tE_err}
		onlineTAPevents[eventName_full] = eventDict
		print "Obtained event dictionary: %s" % (str(eventDict))
	print "Obtained online TAP table: %s" % (str(onlineTAPevents))

"""
def compareList(triggerListFilename=""):
	#for testing
	if triggerListFilename == "":
		triggerList = [{"name": "OGLE-2016-BLG-0220"}, {"name": "OGLE-2016-BLG-0118"}, {"name": "OGLE-2016-BLG-0229"}]
	else:
		triggerList = readTriggerList(triggerListFilename)

	if triggerList == None:
		return

	triggerNames = []
	for event in triggerList:
		triggerNames.append(event["name"])
	TAPtargetNames = []
	for event in TAPtargetList:
		TAPtargetNames.append(event["name"])

	triggerNames_set = set(triggerNames)
	TAPtargetNames_set = set(TAPtargetNames)

	combinedNames_set = triggerNames_set & TAPtargetNames_set
	triggerNamesOnly_set = triggerNames_set - TAPtargetNames_set
	TAPtargetNamesOnly_set = TAPtargetNames_set - triggerNames_set

	print "Events found in both local triggers and online TAP targets:"
	for eventName in combinedNames_set:
		print "Local trigger list data: " + str(triggerList[eventName])
		print "Online TAP list data: " + str(tapList[eventName])
	print

	print "Events found only in local triggers:"
	for eventName in triggerNamesOnly_set:
		print str(triggerList[eventName])
	print

	print "Events found only in online AP targets:"
	for eventName in TAPargetNamesOnly_set:
		print str(TAPtargetList[eventName])
	print
"""

def printOnlineTable():
	TAPnameList = sorted(onlineTAPevents)
	for eventName in TAPnameList:
		eventDict = onlineTAPevents[eventName]
		for item in eventDict:
			print item + ": " + eventDict[item]
		print

def saveTable():
	# Column field names for table
	fieldnames = ["name_TAP", "priority_TAP", "mag_TAP", "tE_TAP", "tE_err_TAP"]

	# if csv file does NOT yet exist, open it for writing, sort the online TAP events by name, and store each event dictionary
	# as a row in this sequence
	if not os.path.isfile(TAP_TARGET_TABLE_OUTPUT_FILEPATH):
		print "File does not exist. Opening file for writing..."
		with open(TAP_TARGET_TABLE_OUTPUT_FILEPATH, "w") as f:
			print "File opened for writing."
			writer = csv.DictWriter(f, fieldnames=fieldnames)
			writer.writeheader()
			onlineTAPname_list = sorted(onlineTAPevents)
			print "Sorted online TAP events: " + str(onlineTAPname_list)
			for eventName in onlineTAPname_list:
				eventDict = onlineTAPevents[eventName]
				print "Writing dict to file: " + str(eventDict)
				writer.writerow(eventDict)

	# if file does already exist, read the existing file, get the sorted combined list of names from both online and locally stored events,
	# then write to file, storing each event dictionary from this combined list as a row in sequence. 
	# Store the updated online event dictionary when its available, else keep the local dictionary.
	else: 
		print "File already exists. Opening file for reading..."
		with open(TAP_TARGET_TABLE_OUTPUT_FILEPATH, "r") as f:
			print "File opened for reading."
			reader = csv.DictReader(f)
			
			# get dictionary with names as keys and event dictionaries as values for locally stored events
			localTAPevents ={}
			for row in reader:
				eventName = row["name_TAP"]
				localTAPevents[eventName] = row		

			print "Local TAP events: " + str(localTAPevents)
			print "Online TAP events: " + str(onlineTAPevents)
			# get set-like objects containing event names from local and online dictionaries,
			# then combine their set and sort it into an ordered list
			onlineTAPname_set = onlineTAPevents.viewkeys()
			localTAPname_set = localTAPevents.viewkeys()
			combinedTAPname_list = sorted(onlineTAPname_set | localTAPname_set)
			print "combined set: " + str(onlineTAPname_set | localTAPname_set)
			print "combined TAP name list: " + str(combinedTAPname_list)

		print "Opening file for writing..."
		with open(TAP_TARGET_TABLE_OUTPUT_FILEPATH, "w") as f:
			print "File opened for writing."
			print "combined TAP name list: " + str(combinedTAPname_list)
			writer = csv.DictWriter(f, fieldnames=fieldnames)
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
				print "Writing event dictionary: " + str(eventDict)
				writer.writerow(eventDict)
	
def main():
	updateTable()
	printOnlineTable()
	print "Online TAP events: " + str(onlineTAPevents)
	saveTable()

if __name__== "__main__":
	main()
