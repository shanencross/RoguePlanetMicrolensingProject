def compareEvents(localEvents, onlineEvents):
	# Create set of all event names in local and online events
	unionEventNames_set = localEvents.viewkeys() | onlineEvents.viewkeys()
	
	# sort event names for iteration 
	unionEventNames_list = sorted(unionEventNames_set)
	unionEvents_list = []
	# iterate over events, updating each event with proper local and TAP
	# trigger values, and with the combined set of items from both
	# local and online if event is present in both
	for eventName in unionEventNames_list:
		
		# check for presence of event in local and online list
		inLocal = eventName in localEvents
		inOnline = eventName in onlineEvents

		# get event from local list if available, else get it from online list
		if inLocal:
			event = localEvents[eventName]
		elif inOnline:
			event = onlineEvents[eventName]
		else:
			print "Error: event %s not found in either local or TAP output" % eventName
			continue

		#set flags for whether event is present in local and/or online lists
		event["local trigger"] = inLocal
		event["TAP trigger"] = inOnline

		# combine items from both lists of event is in both
		if inLocal and inOnline:
			event.update(onlineEvents[eventName])

		# add name to event dictionary if not already present
		if "name" not in event:
			event["name"] = eventName

		# add properly modified to ordered list of union event
		# dictionaries
		unionEvents_list.append(event)

	print "Local list:"
	for event in localEvents:
		print event

	print "Online list:"
	for event in onlineEvents:
		print event

	print "Union list:"
	for event in unionEvents_list:
		print event

def main():
	localEvents = {"OGLE-2016-BLG-0229": {"tE_OGLE": "4.8"}, "OGLE-2016-BLG-0220": {"tE_OGLE": "3.4"}, \
				   "OGLE-2016-BLG-0197": {"tE_OGLE": "4.9"}, "OGLE-2016-BLG-0118": {"tE_OGLE": "3.2"}}

	onlineEvents = {"OGLE-2016-BLG-0220": {"tE_TAP": "3.3"}, "OGLE-2016-BLG-0216": {"tE_TAP": "5.9"}, \
					"OGLE-2016-BLG-0197": {"tE_TAP": "4.8"}, "OGLE-2016-BLG-0195": {"tE_TAP": "1.1"}}

	compareEvents(localEvents, onlineEvents)

if __name__ == "__main__":
	main()
