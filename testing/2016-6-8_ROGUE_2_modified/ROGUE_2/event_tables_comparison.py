"""
event_tables_comparison.py
Author: Shanen Cross
"""
import sys
import os
import csv
import logging

import comparison_table_page_output
from data_collection_and_output import event_data_collection #TEMP - WON'T WORK - HOW TO IMPORT FROM SUBDIR OF PARENT DIR?
import logger_setup

DEBUGGING_MODE = True

if DEBUGGING_MODE:
	LOG_DIR = os.path.join(sys.path[0], "logs_debugging/event_tables_comparison_log")
	if not os.path.exists(LOG_DIR):
		os.makedirs(LOG_DIR)
else:
	LOG_DIR = "/science/robonet/rob/Operations/Logs/2016"
LOG_NAME = "event_tables_comparison_log"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
if DEBUGGING_MODE:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=True, console_output_level = "DEBUG")
else:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=False, console_output_level = "DEBUG")

TEST_ROGUE_FILEPATH = ""

TEST_TAP_DIR = os.path.join(sys.path[0], "TAP/TAP_target_table/")
TEST_TAP_FILENAME = "TAP_target_table.csv"
TEST_TAP_FILEPATH = os.path.join(TEST_TAP_DIR, TEST_TAP_FILENAME)
TEST_COMPARISON_PAGE_FILEPATH = "comparison_table_page_test.html"

UPDATE_TAP_EVENT_WITH_SURVEY_DATA = True

"""
# By default, all fieldnames but those specified here will be included in comparison table
FIELDNAMES_TO_REMOVE_ROGUE = []
FIELDNAMES_TO_REMOVE_TAP = []

# If one of these flag is on, the corresponding list above is ignored, and only the fieldnames
# specified in the corresponding list below are included in the comparison table
KEEP_ONLY_CERTAIN_FIELDNAMES_ROGUE = False
KEEP_ONLY_CERTAIN_FIELDNAMES_TAP = False
FIELDNAMES_TO_KEEP_ROGUE = []
FIELDNAMES_TO_KEEP_TAP = []
"""

def read_ROGUE_table(ROGUE_filepath):
	delimiter = ","

	# If there is no ROGUE table file, return an empty dictionary. 
	# Program should run as normal, just with no ROGUE events.
	if not os.path.isfile(ROGUE_filepath):
		logger.warning("No ROGUE event table file found")
		logger.warning("Filepath: " + str(ROGUE_filepath))
		return {}
	
	with open(ROGUE_filepath, "r") as f:
		logger.debug("ROGUE file opened for reading.")
		reader = csv.DictReader(f, delimiter=delimiter)
		ROGUE_events = {}
		for row in reader:
			logger.debug("Reading the following row:\n" + str(row))
			# If the event has an OGLE name, use this name for dictionary
			if row.has_key("name_OGLE") and row["name_OGLE"] != "":
				final_event_name = row["name_OGLE"]
				logger.debug("The row has an OGLE name: %s" % final_event_name)

			# If the event has a MOA name and no OGLE name, convert it to OGLE if possible;
			# otherwise, leave it the same
			elif row.has_key("name_MOA") and row["name_MOA"] != "":
				initial_event_name = row["name_MOA"]
				logger.debug("The row has a MOA name: %s" % initial_event_name)
				logger.debug("Converting MOA name to OGLE name for comparison...")
				final_event_name = get_comparison_name(initial_event_name)
				logger.debug("MOA name %s converted to OGLE name: %s" % (initial_event_name, final_event_name))
			else:
				logger.warning("Event row has neither MOA nor OGLE name item" % (str(row)))
			
			#Regardless, place the event into the events dictionary
			logger.debug("Placing row in dictionary...")
			ROGUE_events[final_event_name] = row
			logger.debug("Current dictionary:\n" + str(ROGUE_events))

		logger.debug("Final ROGUE events dictionary: "  + str(ROGUE_events))
		return ROGUE_events

def read_TAP_table(TAP_filepath):
	# If there is no TAP table file, return an empty dictionary. 
	# Program should run as normal, just with no TAP events.
	if not os.path.isfile(TAP_filepath):
		logger.warning("Warning: No TAP event table file found")
		logger.warning("Filepath: " + str(TAP_filepath))
		return {}

	delimiter = ","
	with open(TAP_filepath, "r") as f:
		reader = csv.DictReader(f, delimiter=delimiter)
		TAP_events = {}
		for row in reader:
			# Get name listed on TAP and remove the "name_TAP" key, 
			# since we'll just use name_OGLE and name_MOA on the combined table
			initial_event_name = row.pop("name_TAP")

			# If the event is OGLE, leave it unchanged
			# Also add name value to OGLE name key
			if initial_event_name[:4] == "OGLE":
				final_event_name = initial_event_name
				row["name_OGLE"] = final_event_name

			# If the event is MOA, convert it to its OGLE counterpart if possible;
			# otherwise leave it the same
			# Also add name value to MOA name key,
			# and to OGLE name key if event is OGLE after attempting conversion
			elif initial_event_name[:3] == "MOA":
				# TAP MOA events are stored with 4-digit event numbers (e.g. MOA-2016-BLG-0123),
				# but they are listed with 3 digits in most contexts, so we convert them to
				# 3-digit event number strings (e.g. MOA-2016-BLG-123)
				name_MOA = convert_TAP_MOA_numbering(initial_event_name)
				row["name_MOA"] = name_MOA
				final_event_name = get_comparison_name(name_MOA)
				if final_event_name[:4] == "OGLE":
					row["name_OGLE"] = final_event_name
			else:
				"Error: somehow the event, %s, starts with neither MOA nor OGLE prefixes." % (initial_event_name)
				continue

			# Regardless, place the event into the events dictionary
			TAP_events[final_event_name] = row

		return TAP_events

def convert_TAP_MOA_numbering(event_name):
	"""Converts MOA name with a 4-digit event number (e.g. MOA-2016-BLG-0123)
	to a MOA name with a 3-digit event number (e.g. MOA-2016-BLG-123).
	TAP MOA names are stored with 4 digits, but elsewhere 3 digits are used."""

	name_base = event_name[:13]
	name_number = float(event_name[13:])
	name_number_str = "%03d" % name_number
	name_MOA = name_base + name_number_str
	return name_MOA

# Name parameter format: "MOA-2016-BLG-123"
# Assume event is a MOA event
# Convert full MOA name to full OGLE name if available; otherwise return original full MOA name
def get_comparison_name(event_name):
	# Pass name to MOA-to-OGLE conversion function, which returns None if there is no conversion counterpart
	event_name_converted = event_data_collection.convert_event_name(event_name)
	
	# If the event had no conversion counterpart, return the original full name unchanged as the comparison
	if event_name_converted == None:
		comparison_name = event_name
	# If the event was converted, construct the full name for the new converted name and return that as the comparison name
	else:
		comparison_name = event_name_converted
	
	return comparison_name

def compare_tables(ROGUE_filepath, TAP_filepath):
	logger.info("Reading in ROGUE events...")
	ROGUE_events = read_ROGUE_table(ROGUE_filepath)
	logger.info("Reading in TAP events...")
	TAP_events = read_TAP_table(TAP_filepath)
	logger.info("Comparing, and generating combined lists...")
	combined_events_list = compare_event_dicts(ROGUE_events, TAP_events)
	return combined_events_list

def compare_event_dicts(ROGUE_events, TAP_events):

	# Create combined set of all event names in ROGUE and TAP events
	combined_event_names_set = ROGUE_events.viewkeys() | TAP_events.viewkeys()
	
	# sort event names for iteration 
	combined_event_names_list = sorted(combined_event_names_set)
	combined_events_list = []
	# iterate over events, updating each event with proper ROGUE and TAP
	# trigger values, and with the combined set of items from both
	# ROGUE and TAP if event is present in both
	for event_name in combined_event_names_list:
		
		# check for presence of event in ROGUE and TAP list
		in_ROGUE = event_name in ROGUE_events
		in_TAP = event_name in TAP_events

		# get event from ROGUE list if available, else get it from TAP list
		if in_ROGUE:
			event = ROGUE_events[event_name]
			"""
			if KEEP_ONLY_CERTAIN_FIELDNAMES_ROGUE:
				keep_only_certain_fieldnames(event, FIELDNAMES_TO_KEEP_ROGUE)
			else:
				remove_fieldnames(event, FIELDNAMES_TO_REMOVE_ROGUE)
			"""
		elif in_TAP:
			event = TAP_events[event_name]
			"""
			if KEEP_ONLY_CERTAIN_FIELDNAMES_TAP:
				keep_only_certain_fieldnames(event, FIELDNAMES_TO_KEEP_TAP)
			else:
				remove_fieldnames(event, FIELDNAMES_TO_REMOVE_TAP)
			"""
		else:
			logger.warning("Error: event %s not found in either ROGUE or TAP output" % event_name)
			continue

		#set flags for whether event is present in ROGUE and/or TAP lists
		event["ROGUE trigger"] = in_ROGUE
		event["TAP trigger"] = in_TAP

		# combine items from both lists if event is in both
		if in_ROGUE and in_TAP:
			event.update(TAP_events[event_name])

		# If event is from TAP alone and has an OGLE comparison name, it does not contain MOA values
		# even if they are available.
		# So we obtain the MOA and/or OGLE values, depending on what is available, and update the event
		# dictionary with them.
		if in_TAP and not in_ROGUE and UPDATE_TAP_EVENT_WITH_SURVEY_DATA:
			update_TAP_only_event(event)

		# add properly modified event to ordered list of combined event
		# dictionaries
		combined_events_list.append(event)

	"""
	print "ROGUE list:"
	for event in ROGUE_events:
		print event

	print "TAP list:"
	for event in TAP_events:
		print event

	print "Combined list:"
	for event in combined_events_list:
		print event
	"""

	return combined_events_list

def update_TAP_only_event(event):
	"""Update TAP only event with data from survey(s) and/or ARTEMIS."""

	# Collect OGLE data if available
	if event.has_key("name_OGLE") and event["name_OGLE"] != "":
		logger.debug("Obtaining OGLE data for TAP event...")
		try:
			event_update_OGLE = event_data_collection.collect_data_OGLE(event["name_OGLE"])
			event.update(event_update_OGLE)
			logger.debug("OGLE data retrieved.")
		except Exception as ex:
			logger.warning("Exception obtaining OGLE data for TAP event.")
			logger.warning(ex)
			raise

		logger.debug("Obaining ARTEMIS OGLE data for TAP event...")
		try:
			event_update_ARTEMIS_OGLE = event_data_collection.collect_data_ARTEMIS(event["name_OGLE"])
			event.update(event_update_ARTEMIS_OGLE)
			if event_update_ARTEMIS_OGLE != {}:
				logger.debug("ARTEMIS OGLE data retrieved.")
		except Exception as ex:
			logger.warning("Exception obtaining ARTEMIS OGLE data for TAP event.")
			raise

		# Needs this because we don't check OGLE events for corresponding MOA events
		# when reading in the TAP file. Conversely, a MOA event will always have an 
		# OGLE name key if available.
		try:
			name_MOA = event_data_collection.convert_event_name(event["name_OGLE"])
			if name_MOA != None:
				event["name_MOA"] = name_MOA
		except Exception as ex:
			logger.warning("Exception converting event name from OGLE to MOA.")
			logger.warning(ex)
			raise

	# Collect MOA data if available
	if event.has_key("name_MOA") and event["name_MOA"] != "":
		logger.debug("Obtaining MOA data for TAP event...")		
		try:
			event_update_MOA = event_data_collection.collect_data_MOA(event["name_MOA"])
			event.update(event_update_MOA)
			logger.debug("MOA data retrieved.")
		except Exception as ex:
			logger.warning("Exception obtaining MOA data for TAP event.")
			raise

		logger.debug("Obtaining ARTEMIS MOA data for TAP event...")
		try:
			event_update_ARTEMIS_MOA = event_data_collection.collect_data_ARTEMIS(event["name_MOA"])
			event.update(event_update_ARTEMIS_MOA)
			if event_update_ARTEMIS_MOA != {}:
				logger.debug("ARTEMIS MOA data retrieved.")
		except Exception as ex:
			logger.warning("Exception obtaining ARTEMIS MOA data for TAP event.")
			raise
"""
def remove_fieldnames(event, fieldnames_to_remove):
	# Remove specified fieldnames from event dictionary. 
	# Allows us to omit columns from .csv files that we don't want to include on table.

	for fieldname in fieldnames_to_remove:
		if event.has_key(fieldname):
			del event[fieldname]

def keep_only_certain_fieldnames(event, fieldnames_to_keep):
	# Remove all fieldnames except a certain set of fieldnames.
	# Allows us to specify exactly which columns from the .csv file
	# we wish to include.

	trimmed_event = {}
	for fieldname in fieldnames_to_remove:
		if event.has_key(fieldname):
			trimmed_event = event[fieldname]

	event = trimmed_event
"""

def compare_and_output(ROGUE_filepath, TAP_filepath, comparison_page_filepath):
	logger.info("------------------------------------------------------------------------------")
	logger.info("Comparing tables...")
	combined_events_list = compare_tables(ROGUE_filepath, TAP_filepath)
	logger.info("Outputting comparison page...")
	comparison_table_page_output.output_comparison_page(combined_events_list, comparison_page_filepath)
	logger.info("------------------------------------------------------------------------------")

def test_dicts():
	ROGUE_events = {"OGLE-2016-BLG-0229": {"name_OGLE":"OGLE-2016-BLG-0229", "tE_OGLE":"4.8"}, \
				   "OGLE-2016-BLG-0220": {"name_OGLE":"OGLE-2016-BLG-0220", "tE_OGLE":"3.4"}, \
				   "OGLE-2016-BLG-0197": {"name_OGLE":"OGLE-2016-BLG-0197", "tE_OGLE":"4.9"}, \
				   "OGLE-2016-BLG-0118": {"name_OGLE":"OGLE-2016-BLG-0118", "tE_OGLE":"3.2"}, \
				   "MOA-2016-BLG-133": {"name_MOA":"MOA-2016-BLG-133", "tE_MOA":"1.8"}, \
				   "MOA-2016-BLG-133": {"name_MOA":"MOA-2016-BLG-133", "ID_MOA":"gb4-R-8-62452", "tE_MOA":"1.8"}, \
				   "OGLE-2016-BLG-0524": {"name_MOA":"MOA-2016-BLG-119", "name_OGLE":"OGLE-2016-BLG-0524", \
										  "ID_MOA":"gb9-R-8-44792", "tE_MOA":"1.8", "tE_OGLE":"1.9"}}

	TAP_events = {"OGLE-2016-BLG-0220": {"name_OGLE":"OGLE-2016-BLG-0220", "tE_OGLE":"3.3"}, \
				   "OGLE-2016-BLG-0216": {"name_OGLE":"OGLE-2016-BLG-0216", "tE_OGLE":"5.9"}, \
				   "OGLE-2016-BLG-0197": {"name_OGLE":"OGLE-2016-BLG-0197", "tE_OGLE":"4.8"}, \
				   "OGLE-2016-BLG-01195": {"name_OGLE":"OGLE-2016-BLG-0195", "tE_OGLE":"1.1"}}

	combined_events_list = compare_event_dicts(ROGUE_events, TAP_events)
	comparison_table_page_output.output_comparison_page(combined_events_list, TEST_COMPARISON_PAGE_FILEPATH)

def test_filepaths():
	compare_and_output(TEST_ROGUE_FILEPATH, TEST_TAP_FILEPATH, TEST_COMPARISON_PAGE_FILEPATH)

def main():
	#test_dicts()
	test_filepaths()

if __name__ == "__main__":
	main()
