# eventTablesComparison.py

import csv

import comparisonTablePageOutput
from dataCollectionAndOutput import eventDataCollection #TEMP - WON'T WORK - HOW TO IMPORT FROM SUBDIR OF PARENT DIR?

TEST_ROGUE_FILEPATH = ""
TEST_TAP_FILEPATH = ""
TEST_COMPARISON_PAGE_FILEPATH = "comparisonTablePage_test.html"

def readROGUEtable(ROGUEfilepath):
	delimiter = ", "
	with open(ROGUEfilepath, "r") as f:
		reader = csv.DictReader(f, delimiter=delimiter)
		
		ROGUEevents = {}
		for row in reader:
			
			# If the event has an OGLE name, use this name for dictionary
			if row.has_key("name_OGLE"):
				finalEventName = row["name_MOA"]

			# If the event has a MOA name and no OGLE name, convert it to OGLE if possible;
			# otherwise, leave it the same
			elif row.has_key("name_MOA"):
				initialEventName = row["name_OGLE"]
				finalEventname = getComparisonName(initialEventName)
			
			#Regardless, place the event into the events dictionary
			ROGUEevents[finalEventName] = row					

		return ROGUEevents

def readTAPtable(TAPfilepath):
	delimiter = ", "
	with open(TAPfilepath, "r") as f:
		reader = csv.DictReader(f, delimiter=delimiter)
		TAPevents = {}
		for row in reader:
			# Get name listed on TAP and remove the "name_TAP" key, 
			# since we'll just use name_OGLE and name_MOA on the combined table
			initialEventName = row.pop("name_TAP")

			# If the event is OGLE, leave it unchanged
			# Also add name value to OGLE name key
			if initialEventName[:4] == "OGLE":
				finalEventName = initialEventName
				row["name_OGLE"] = finalEventName

			# If the event is MOA, convert it to its OGLE counterpart if possible;
			# otherwise leave it the same
			# Also add name value to MOA name key,
			# and to OGLE name key if event is OGLE after attempting conversion
			elif initialEventName[:3] == "MOA":
				row["name_MOA"] = initialEventName
				finalEventName = getComparisonName(initialEventName)
				if finalEventName[:4] == OGLE:
					row["name_OGLE"] = finalEventName
			else:
				"Error: somehow the event, %s, starts with neither MOA nor OGLE prefixes." % (initialEventName)
				continue

			# Regardless, place the event into the events dictionary
			TAPevents[finalEventName] = row

		return TAPevents

# Name parameter format: "MOA-2016-BLG-123"
# Assume event is a MOA event
# Convert full MOA name to full OGLE name if available; otherwise return original full MOA name
def getComparisonName(eventName_full):
	# Get the shortened event name witout survey prefix, e.g. MOA-2016-BLG-123 shortens to 2016-BLG-123
	eventName_short = eventName_full[4:]

	# Pass shortened name to MOA-to-OGLE conversion function, which returns None if there is no conversion counterpart
	eventNameConverted_short = eventDataCollection.convertEventName(eventName_full, MOAtoOGLE=True)
	
	# If the event had no conversion counterpart, return the original full name unchanged as the comparison
	if eventNameConverted_short == None:
		comparisonName = eventname_full
	# If the event was converted, construct the full name for the new converted name and return that as the comparison name
	else:
		comparisonName = "OGLE-" + eventNameConverted_short
	
	return comparisonName
	

def compareTables(ROGUEfilepath, TAPfilepath):
	ROGUEevents = readROGUEtable(ROGUEfilepath)
	TAPevents = readTAPtable(TAPfilepath)
	compareEventDicts(ROGUEevents, TAPevents)

def compareEventDicts(ROGUEevents, TAPevents):
	# Create combined set of all event names in ROGUE and TAP events
	combinedEventNames_set = ROGUEevents.viewkeys() | TAPevents.viewkeys()
	
	# sort event names for iteration 
	combinedEventNames_list = sorted(combinedEventNames_set)
	combinedEvents_list = []
	# iterate over events, updating each event with proper ROGUE and TAP
	# trigger values, and with the combined set of items from both
	# ROGUE and TAP if event is present in both
	for eventName in combinedEventNames_list:
		
		# check for presence of event in ROGUE and TAP list
		inROGUE = eventName in ROGUEevents
		inTAP = eventName in TAPevents

		# get event from ROGUE list if available, else get it from TAP list
		if inROGUE:
			event = ROGUEevents[eventName]
		elif inTAP:
			event = TAPevents[eventName]
		else:
			print "Error: event %s not found in either ROGUE or TAP output" % eventName
			continue

		#set flags for whether event is present in ROGUE and/or TAP lists
		event["ROGUE trigger"] = inROGUE
		event["TAP trigger"] = inTAP

		# combine items from both lists if event is in both
		if inROGUE and inTAP:
			event.update(TAPevents[eventName])

		# add properly modified to ordered list of combined event
		# dictionaries
		combinedEvents_list.append(event)

	print "ROGUE list:"
	for event in ROGUEevents:
		print event

	print "TAP list:"
	for event in TAPevents:
		print event

	print "Combined list:"
	for event in combinedEvents_list:
		print event

	return combinedEvents_list

def compareAndOutput(ROGUEfilepath, TAPfilepath, comparisonPageFilepath):
	combinedEvents_list = compareTables(ROGUEfilepath, TAPfilepath)
	comparisonTablePageOutput.outputComparisonPage(combinedEvents_list, comparisonPageFilepath)

def test_dicts():
	ROGUEevents = {"OGLE-2016-BLG-0229": {"name_OGLE":"OGLE-2016-BLG-0229", "tE_OGLE": "4.8"}, \
				   "OGLE-2016-BLG-0220": {"name_OGLE":"OGLE-2016-BLG-0220", "tE_OGLE": "3.4"}, \
				   "OGLE-2016-BLG-0197": {"name_OGLE":"OGLE-2016-BLG-0197", "tE_OGLE": "4.9"}, \
				   "OGLE-2016-BLG-0118": {"name_OGLE":"OGLE-2016-BLG-0118", "tE_OGLE": "3.2"}}

	TAPevents = {"OGLE-2016-BLG-0220": {"name_OGLE":"OGLE-2016-BLG-0220", "tE_OGLE": "3.3"}, \
				   "OGLE-2016-BLG-0216": {"name_OGLE":"OGLE-2016-BLG-0216", "tE_OGLE": "5.9"}, \
				   "OGLE-2016-BLG-0197": {"name_OGLE":"OGLE-2016-BLG-0197", "tE_OGLE": "4.8"}, \
				   "OGLE-2016-BLG-01195": {"name_OGLE":"OGLE-2016-BLG-0195", "tE_OGLE": "1.1"}

	combinedEvents_list = compareEventDicts(ROGUEevents, TAPevents)
	comparisonTablePageOutput.outputComparisonPage(combinedEvents_list, comparisonPageFilepath)

def test_filepaths():
	compareAndOutput(TEST_ROGUE_FILEPATH, TEST_TAP_FILEPATH, TEST_COMPARISON_PAGE_FILEPATH)

def main():
	test_dicts()

if __name__ == "__main__":
	main()
