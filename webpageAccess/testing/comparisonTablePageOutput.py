"""
comparisonTablePageOutput.py
Author: Shanen Cross
Purpose: Given list of combined ROGUE/TAP dictionaries from compareEventTables.py, ouput comparison table HTML page. 
"""
from datetime import datetime

TEST_EVENT_LIST = [{"name_MOA":"MOA-2015-BLG-123", "ID_MOA":"gb19-R-2-7179", "ROGUE trigger":"yes", "TAP trigger":"no"}, \
				   {"name_OGLE":"OGLE-2015-BLG-0123", "ROGUE trigger":"yes", "TAP trigger":"yes"}, \
				   {"name_OGLE":"OGLE-2016-BLG-0224", "ROGUE trigger":"no", "TAP trigger":"yes"}]
TEST_COMPARISON_PAGE_FILEPATH = "tableOutput_test.html"

"""
ROGUE fieldnames: ["name_MOA", "name_OGLE", "ID_MOA", "RA_MOA", "Dec_MOA", "tE_MOA", "tE_err_MOA", "tE_OGLE", "tE_err_OGLE", "tE_ARTEMIS_MOA", "tE_err_ARTEMIS_MOA", \
				  "tE_ARTEMIS_OGLE", "tE_err_ARTEMIS_OGLE", "u0_MOA", "u0_err_MOA", "u0_OGLE", "u0_err_OGLE", "u0_ARTEMIS_MOA", "u0_err_ARTEMIS_MOA", \
				  "u0_ARTEMIS_OGLE", "u0_err_ARTEMIS_OGLE", "mag_MOA", "mag_err_MOA"] 

TAP fieldnames:
				  ["name_MOA", "name_OGLE", "priority_TAP", "mag_TAP", "tE_TAP", "tE_err_TAP"]
"""

MOA_DIR_BASE = "https://it019909.massey.ac.nz/moa/alert" 
OGLE_DIR_BASE = "http://ogle.astrouw.edu.pl/ogle4/ews/"

# List of fields (dictionary keys) to be used as column headers in the table. 
# They must match the key names for the combined ROGUE/TAP event dictionaries. 
# Can omitt any keys/fields we want to exclude from the table.
# If an event dictionary lacks one of these keys (i.e. an event has only a MOA name, and no OGLE name), "N/A" will be
# printed in the corresponding table entry.
COMBINED_FIELDNAMES = ["name_MOA", "name_OGLE", "RA_MOA", "Dec_MOA", "ROGUE trigger", "TAP trigger", "priority_TAP", "tE_TAP", "tE_err_TAP", "tE_MOA", \
					   "tE_err_MOA", "tE_OGLE", "tE_err_OGLE", "tE_ARTEMIS_MOA", "tE_err_ARTEMIS_MOA", "tE_ARTEMIS_OGLE", "tE_err_ARTEMIS_OGLE", "u0_MOA", \
					   "u0_err_MOA", "u0_OGLE", "u0_err_OGLE", "u0_ARTEMIS_MOA", "u0_err_ARTEMIS_MOA", "u0_ARTEMIS_OGLE", "u0_err_ARTEMIS_OGLE", "mag_MOA", \
					   "mag_err_MOA"] 

def outputComparisonPage(eventList, comparisonPageFilepath):
	"""Given sorted list of events and output path, print comparison table to file."""

	with open(comparisonPageFilepath, "w") as myFile:
		printPageStart(myFile)
		printEventList(eventList, myFile)
		printPageEnd(myFile)

def printEventList(eventList, myFile):
	"""Print row for each event within table."""

	for event in eventList:
		print >> myFile, """<TR>"""
		printEvent(event, myFile)
		print >> myFile, """</TR>"""

def printEvent(event, myFile):
	"""Print row for an individual event."""
	
	# COMBINED_FIELDNAMES dictates which keys are to be included as fields. Can exclude data we don't want in the final table
	# from this field list as desired. If dictionary entry is not found for one of these fields, will output entry "N/A".
	for key in COMBINED_FIELDNAMES:

		# Makes sure the event has the data item.
		if event.has_key(key):

			# If the field is either the MOA name or OGLE name,
			# output the fieldname as a link to the event page.
			if key == "name_MOA" or key == "name_OGLE":
				entry = "<a href=%s>%s</a>" % (getURL(event, key), event[key])

			# Otherwise, output . Later,
			else:
				entry = event[key]
		#If field data item is not in event, output "N/A".
		else:
			entry = "N/A"
		print >> myFile, """<TD>%s</TD>""" % entry

def getURL(event, nameKey):
	"""Get the URL for an event from event dictionary and the name key to specify which survey's name we want."""

	# The event's year is part of the MOA URL, and may be part of the OGLE one
	eventYear = getEventYear(event[nameKey])

	# If we want a MOA name, construct URL from event's year and MOA ID
	if nameKey == "name_MOA":
		MOA_dir = MOA_DIR_BASE + eventYear + "/"
		if event.has_key("ID_MOA"):
			eventURL = MOA_dir + "display.php?id=" + event["ID_MOA"]
		else:
			print "Warning: No MOA ID found for event in dictionary. Cannot construct MOA URL. URL left as empty string."
			eventURL = ""

	# If we want an OGLE name, construct the URL from its event name with year prefix removed.
	# If event's year is older than current year, subdirectory of the event year is added on 
	# to OGLE base URL directory.
	elif nameKey == "name_OGLE":
		currentYear = str(datetime.utcnow().year)
		OGLE_dir = OGLE_DIR_BASE

		if currentYear != eventYear:
			OGLE_dir += eventYear + "/"
		nameInURL = event[nameKey][10:].lower()
		eventURL = OGLE_dir + nameInURL + ".html"

	# Return empty string if asked for something other than a MOA or OGLE name.
	else:
		print "Error: Event name key %s does not match either name_MOA or name_OGLE keys" % (nameKey)
		print "Event: %s" % (str(event))
		eventURL = ""

	return eventURL

def getEventYear(eventName):
	"""Get the year of the event from its name."""

	year = eventName.split("-")[1]
	return year

def printPageStart(myFile):
	"""Output beginning of HTML page file, including opening tag for table and table headers."""

	print >> myFile, \
"""\
<html>
<title>Target Comparison Table: ROGUE vs. TAP</title><head><STYLE type="text/css">strong.topnav {background: #EFF5FB; color: #0000FF; text-align: center; padding-bottom: 0.2em; font-family: arial, helvetica, times; font-size: 10pt}a.plain {text-decoration:none; color: #0000FF} a:visited {text-decoration:none; color: blue} a.plain:hover {text-decoration:none; background: #819FF7; color: white}BODY { font-family: arial, helvetica, times; background: #FFFFFF; margin-left:0.2em; margin-right: 1em}.textheading {text-align: right; width: 70%; color: #819FF7; font-family: arial, helvetica, times; margin-top: 1.5em}.tablehead {color: #AAAAA; text-align: center; font-family: arial, helvetica, times; font-weight: bold}tablecontent {margin-top: 0.3em; margin-left: 0.2em; margin-bottom: 0.2em; font-family: arial, helvetica, times}.generic {font-family: arial, helvetica, times}.table {font-family: arial, helvetica, times; text-align: center}a:link {text-decoration:none;} a:visited {text-decoration:none; color: blue} a:hover {text-decoration:none; color: #819FF7}</STYLE></head><body>
<H2> Target Comparison Table: ROGUE vs. TAP</H2>
Notes:<BR>
Events triggered by only TAP will have N/A entries for MOA, OGLE, and ARTEMIS values, even if they exist.<BR>
This is because the TAP csv files only store the TAP data, while the ROGUE csv files store the MOA, OGLE, and ARTEMIS data.<BR>
Likewise, TAP-only events have no working MOA URLs, because the csv files do not contain the MOA ID which is needed to construct those URLs.<BR>
Comparison script should be updated to collect this additional data for TAP-only events.<BR>
<BR>
Also, data from ROGUE for a particular (MOA, OGLE, and ARTEMIS values) has not been updated since that event triggered. Check survey sites for updated data.<BR>
The TAP data, on the other hand, is regularly updated, but this table only updates when ROGUE triggers on an event.<BR>
So the TAP data dates from when ROGUE last triggered on an event.<BR>
Any TAP events more recent than the latest ROGUE trigger are thus not listed.<BR>
<BR>
<TABLE cellpadding="4" style="border: 1px solid #000000; border-collapse: collapse;" border="1">
<TR>\
"""
	# Output unmodified dictionary keys as column headers. May want to modify this for aesthetic reasons later.
	# (e.g. remove underscores, both survey name suffixes in parentheses, etc.)
	for fieldname in COMBINED_FIELDNAMES:
		print >> myFile, \
"""\
  <TH>%s</TH>
""" % (fieldname)

	print >> myFile, \
"""\
 </TR>
 <TR>\
"""

def printPageEnd(myFile):
	"""Output end of HTML page file, including closing table tag."""
	
	print >> myFile, """</TABLE>"""

def outputTest():
	"""Output a test comparison page using hardcoded event list and test output filepath."""
	outputComparisonPage(TEST_EVENT_LIST, TEST_COMPARISON_PAGE_FILEPATH)

def main():
	outputTest()

if __name__ == "__main__":
	main()
