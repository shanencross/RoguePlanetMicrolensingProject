"""
comparison_table_page_output.py
@author: Shanen Cross
Purpose: Given list of combined ROGUE/TAP dictionaries from compareEventTables.py, ouput comparison table HTML page. 
"""
import sys
import os
from datetime import datetime
import logging

import logger_setup

DEBUGGING_MODE = False

LOG_DIR = os.path.join(sys.path[0], "logs/comparison_table_page_output_log")
LOG_NAME = "comparison_table_page_output_log"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
if DEBUGGING_MODE:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=True, console_output_level = "DEBUG")
else:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=False, console_output_level = "DEBUG")

TEST_EVENT_LIST = [{"name_MOA":"MOA-2015-BLG-123", "ID_MOA":"gb19-R-2-7179", "ROGUE trigger":"yes", "TAP trigger":"no"}, \
				   {"name_OGLE":"OGLE-2015-BLG-0123", "ROGUE trigger":"yes", "TAP trigger":"yes"}, \
				   {"name_OGLE":"OGLE-2016-BLG-0224", "ROGUE trigger":"no", "TAP trigger":"yes"}]
TEST_COMPARISON_PAGE_FILEPATH = "table_output_test.html"

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
COMBINED_FIELDNAMES = ["name_MOA", "name_OGLE", "ROGUE trigger", "TAP trigger", "RA_MOA", "Dec_MOA", "RA_OGLE", "Dec_OGLE", \
					   "RA_TAP", "Dec_TAP", "priority_TAP", "tE_TAP", "tE_err_TAP", "tE_MOA", "tE_err_MOA", "tE_OGLE", \
					   "tE_err_OGLE", "tE_ARTEMIS_MOA", "tE_err_ARTEMIS_MOA", "tE_ARTEMIS_OGLE", "tE_err_ARTEMIS_OGLE", \
					   "u0_MOA", "u0_err_MOA", "u0_OGLE", "u0_err_OGLE", "u0_ARTEMIS_MOA", "u0_err_ARTEMIS_MOA", \
					   "u0_ARTEMIS_OGLE", "u0_err_ARTEMIS_OGLE", "mag_MOA", "mag_err_MOA"] 

def output_comparison_page(event_list, comparison_page_filepath):
	logger.info("------------------------------------------------------------------------------")
	"""Given sorted list of events and output path, print comparison table to file."""

	with open(comparison_page_filepath, "w") as my_file:
		print_page_start(my_file)
		print_event_list(event_list, my_file)
		print_page_end(my_file)

	logger.info("------------------------------------------------------------------------------")

def print_event_list(event_list, my_file):
	"""Print row for each event within table."""
	logger.debug("Outputting list of events to page...")
	logger.debug("List:\n" + str(event_list))
	for event in event_list:
		print >> my_file, """<TR>"""
		print_event(event, my_file)
		print >> my_file, """</TR>"""

def print_event(event, my_file):
	"""Print row for an individual event."""

	logger.debug("Printing event...")
	logger.debug("Event:\n" + str(event))
	# COMBINED_FIELDNAMES dictates which keys are to be included as fields. Can exclude data we don't want in the final table
	# from this field list as desired. If dictionary entry is not found for one of these fields, will output entry "N/A".
	for key in COMBINED_FIELDNAMES:

		# Makes sure the event has the data item.
		if event.has_key(key) and event[key] != "":

			# If the field is either the MOA name or OGLE name,
			# output the fieldname as a link to the event page.
			if key == "name_MOA" or key == "name_OGLE":
				entry = "<a href=%s>%s</a>" % (get_URL(event, key), event[key])

			# Otherwise, output . Later,
			else:
				entry = event[key]
		#If field data item is not in event, output "N/A".
		else:
			entry = "N/A"
		print >> my_file, """<TD>%s</TD>""" % entry

def get_URL(event, name_key):
	"""Get the URL for an event from event dictionary and the name key to specify which survey's name we want."""

	# The event's year is part of the MOA URL, and may be part of the OGLE one
	event_year = get_event_year(event[name_key])

	# If we want a MOA name, construct URL from event's year and MOA ID
	if name_key == "name_MOA":
		MOA_dir = MOA_DIR_BASE + event_year + "/"
		if event.has_key("ID_MOA") and event["ID_MOA"] != "":
			event_URL = MOA_dir + "display.php?id=" + event["ID_MOA"]
		else:
			logger.warning("No MOA ID found for event in dictionary. Cannot construct MOA URL. URL left as empty string.")
			event_URL = ""

	# If we want an OGLE name, construct the URL from its event name with year prefix removed.
	# If event's year is older than current year, subdirectory of the event year is added on 
	# to OGLE base URL directory.
	elif name_key == "name_OGLE":
		current_year = str(datetime.utcnow().year)
		OGLE_dir = OGLE_DIR_BASE

		if current_year != event_year:
			OGLE_dir += event_year + "/"
		name_in_URL = event[name_key][10:].lower()
		event_URL = OGLE_dir + name_in_URL + ".html"

	# Return empty string if asked for something other than a MOA or OGLE name.
	else:
		logger.warning("Event name key %s does not match either name_MOA or name_OGLE keys" % (name_key))
		logger.warning("Event: %s" % (str(event)))
		event_URL = ""

	return event_URL

def get_event_year(eventName):
	"""Get the year of the event from its name."""

	year = eventName.split("-")[1]
	return year

def print_page_start(my_file):
	"""Output beginning of HTML page file, including opening tag for table and table headers."""

	logger.debug("Outputting start of page...")
	print >> my_file, \
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
		print >> my_file, \
"""\
  <TH>%s</TH>
""" % (fieldname)

	print >> my_file, \
"""\
 </TR>
 <TR>\
"""

def print_page_end(my_file):
	"""Output end of HTML page file, including closing table tag."""
	
	logger.debug("Outputting end of page...")
	print >> my_file, """</TABLE>"""

def output_test():
	"""Output a test comparison page using hardcoded event list and test output filepath."""
	output_comparison_page(TEST_EVENT_LIST, TEST_COMPARISON_PAGE_FILEPATH)

def main():
	output_test()

if __name__ == "__main__":
	main()
