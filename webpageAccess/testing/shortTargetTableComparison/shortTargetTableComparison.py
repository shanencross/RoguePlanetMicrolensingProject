"""
shortTargetTableComparison.py
Purpose: Download Markus's TAP Kepler Short Candidate List from the the robonet server, then compare to stored list of event triggers from webpageAcesss.py
and store comparison information.
Author: Shanen Cross
Date: 2016-03-18
"""
import requests
import os
from bs4 import BeautifulSoup

# local script imports
from compareEventTables import compareEvents

FILENAME = "targetListComparison.txt"
TAP_TARGET_TABLE_URL = "http://robonet.lcogt.net/temp/tap1mlist_kepler_short.html"
TEST_TAP_TARGET_TABLE_FILEPATH =  "TAP - potential Kepler events.html"
TAPtargets = []

# set up and create ouptut directory and filename for TAP target table
TAP_TARGET_TABLE_OUTPUT_FILENAME + "TAP_target_table.csv"
TAP_TARGET_TABLE_OUTPUT_DIR = os.path.join(sys.path[0], "TAPtargetTable")
TAP_TARGET_TABLE_OUTPUT_FILEPATH = os.path.join(TAP_TARGET_TABLE_OUTPUT_DIR, TAP_TARGET_TABLE_OUTPUT_FILENAME)
if not os.path.exists(TAP_TARGET_TABLE_OUTPUT_DIR):
	os.makedirs(TAP_TARGET_TABLE_OUTPUT_DIR)

LOCAL_TEST_ONLY = False

def updateTable():
	if LOCAL_TEST_ONLY:
		with open(TEST_TAP_TARGET_TABLE_FILEPATH, 'r') as pageFile:
			targetListSoup = BeautifulSoup(pageFile, "lxml"))	 
	else:
		targetListSoup = BeautifulSoup(requests.get(TAP_TARGET_TABLE_URL, verify=False).content, "lxml")

	events = targetListSoup.find("table").find_all("tr")[1:]
	global TAPtargetList
	TAPtargetList = [] #empty list in case it was filled previously
	for event in events:
		eventLines = event.find_all("td")
		eventName = eventLines[0].string
		eventPriority = eventLines[7].string
		eventMag = eventLines[9].string
		event_tE = eventLines[15].string
		event_tE_err = eventLines[16].string
		eventDict = {"name_TAP": eventName, "priority": eventPriority, "mag_TAP": eventMag, "tE_TAP": event_tE, "tE_err_TAP": event_tE_err}
		TAPtargetList.append(eventDict)

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

def readTriggerList(triggerListFilename):
	return

def printTable():
	for eventDict in TAPtargetList:
		for item in eventDict:
			print item + ": " + eventDict[item]
		print

def saveTable():
	with open (

def main():
	updateTable()
	printTable()
	saveTable()

if __name__== "__main__":
	main()
