# eventTablesComparison.py

import csv

import comparisonTablePageOutput

TEST_ROGUE_FILEPATH = ""
TEST_TAP_FILEPATH = ""
TEST_COMPARISON_PAGE_FILEPATH = "comparisonTablePage_test.html"

def readROGUEtable(ROGUEfilepath):
	delimiter = ", "
	with open(ROGUEfilepath, "r") as f:
		reader = csv.DictReader(f, delimiter=delimiter)
		ROGUEevents = []
		for row in reader:
			ROGUEevents.append(row)
		return ROGUEevents

def readTAPtable(TAPfilepath):
	with open(TAPfilepath, "r") as f:
		reader = csv.DictReader(f, delimiter=delimiter)
		TAPevents = []
		for row in reader:
			TAPevents.append(row)
		return TAPevents

def compareTables(ROGUEfilepath, TAPfilepath):
	ROGUEevents = readROGUEtable(ROGUEfilepath)
	TAPevents = readTAPtable(TAPfilepath)
	compareEventLists(ROGUEevents, TAPevents)

def compareEventLists(ROGUEevents, TAPevents):
	# Create set of all event names in ROGUE and TAP events
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

		# add name to event dictionary if not already present
		if "name" not in event:
			event["name"] = eventName

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

def main():
	ROGUEevents = {"OGLE-2016-BLG-0229": {"tE_OGLE": "4.8"}, "OGLE-2016-BLG-0220": {"tE_OGLE": "3.4"}, \
				   "OGLE-2016-BLG-0197": {"tE_OGLE": "4.9"}, "OGLE-2016-BLG-0118": {"tE_OGLE": "3.2"}}

	TAPevents = {"OGLE-2016-BLG-0220": {"tE_TAP": "3.3"}, "OGLE-2016-BLG-0216": {"tE_TAP": "5.9"}, \
					"OGLE-2016-BLG-0197": {"tE_TAP": "4.8"}, "OGLE-2016-BLG-0195": {"tE_TAP": "1.1"}}

	compareEventLists(ROGUEevents, TAPevents)

def test_lists():
	ROGUEevents = {"OGLE-2016-BLG-0229": {"tE_OGLE": "4.8"}, "OGLE-2016-BLG-0220": {"tE_OGLE": "3.4"}, \
				   "OGLE-2016-BLG-0197": {"tE_OGLE": "4.9"}, "OGLE-2016-BLG-0118": {"tE_OGLE": "3.2"}}

	TAPevents = {"OGLE-2016-BLG-0220": {"tE_TAP": "3.3"}, "OGLE-2016-BLG-0216": {"tE_TAP": "5.9"}, \
					"OGLE-2016-BLG-0197": {"tE_TAP": "4.8"}, "OGLE-2016-BLG-0195": {"tE_TAP": "1.1"}}

	combinedEvents_list = compareEventLists(ROGUEevents, TAPevents)
	comparisonTablePageOutput.outputComparisonPage(combinedEvents_list, comparisonPageFilepath)

def test_filepaths():
	ROGUEfilepath = ""
	TAPfilepath = ""

	compareAndOutput(TEST_ROGUE_FILEPATH, TEST_TAP_FILEPATH, TEST_COMPARISON_PAGE_FILEPATH)

if __name__ == "__main__":
	main()
