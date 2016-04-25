"""
reading_master_list.py
@author: Shanen Cross
"""

import sys
import os
import logging

import logger_setup
#import ROGUE

DEBUGGING_MODE = True

# create and set up filepath and directory for logs -
# log dir is subdir of script
#LOG_DIR = os.path.join(sys.path[0], "logs/reading_master_list_log")
LOG_DIR = "/science/robonet/rob/Operations/Logs/2016"
LOG_NAME = "reading_master_list_log"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
if DEBUGGING_MODE:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=True, console_output_level = "DEBUG")
else:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=False, console_output_level = "DEBUG")

if DEBUGGING_MODE:
	EVENT_MASTER_LIST_FILEPATH = os.path.join(sys.path[0], "master_events_list_folder/master_events_list")
else:
	EVENT_MASTER_LIST_FILEPATH = "/science/robonet/rob/Operations/ExoFOP/master_events_list"

NUM_START_INDEX_OGLE = 14
YEAR_START_INDEX_OGLE = 5
YEAR_END_INDEX_OGLE = YEAR_START_INDEX_OGLE + 4

NUM_START_INDEX_MOA = 13
YEAR_START_INDEX_MOA = 4
YEAR_END_INDEX_MOA = YEAR_START_INDEX_MOA + 4

def convert_string_to_boolean(string):
	if string == "False" or string == "Unknown":
		boolean = False
	elif string == "True":
		boolean = True
	else:
		boolean = False
		logger.warning("Tried to convert supposed boolean string %s to boolean, but string was not True, False, or Unknown." % string)
		logger.warning("Setting boolean to False by default.")

	return boolean

def check_event_master_list(local_events):

	if local_events == None:
		return #DEBUG: fix later

	local_event_OGLE = local_events["OGLE"]
	local_event_MOA = local_events["MOA"]
	logger.info ("Most recently checked local OGLE event: %s" % (local_event_OGLE))
	logger.info ("Most recently checked local MOA event: %s" % (local_event_MOA))

	local_year_OGLE = int(local_event_OGLE[YEAR_START_INDEX_OGLE:YEAR_END_INDEX_OGLE])
	local_year_MOA = int(local_event_MOA[YEAR_START_INDEX_MOA:YEAR_END_INDEX_MOA])

	local_num_OGLE = int(local_event_OGLE[NUM_START_INDEX_OGLE:])
	local_num_MOA = int(local_event_MOA[NUM_START_INDEX_MOA:])

	logger.debug("Newest OGLE number: %s" % (str(local_num_OGLE)))
	logger.debug("Newest OGLE year: %s" % (str(local_year_OGLE)))
	logger.debug("Newest MOA number: %s" % (str(local_num_MOA)))
	logger.debug("Newest MOA year: %s" % (str(local_year_MOA)))

	events_to_evaluate = []
	with open(EVENT_MASTER_LIST_FILEPATH, "r") as masterList:
		for line in masterList:
			if line[0] == "#":
				continue
			logger.debug(str(line))

			lineSplit = line.split()
			in_K2_footprint = convert_string_to_boolean(lineSplit[2])
			in_K2_superstamp = convert_string_to_boolean(lineSplit[3])
			during_K2_campaign = convert_string_to_boolean(lineSplit[4])
			name_OGLE = lineSplit[5]
			name_MOA = lineSplit[6]

			if name_OGLE == "None" or name_OGLE == "Unknown":
				year_OGLE = None
				num_OGLE = None
			else:
				year_OGLE = int(name_OGLE[YEAR_START_INDEX_OGLE:YEAR_END_INDEX_OGLE])
				num_OGLE = int(name_OGLE[NUM_START_INDEX_OGLE:])

			if name_MOA == "None" or name_MOA == "Unknown":		
				year_MOA = None
				num_MOA = None
			else:	
				year_MOA = int(name_MOA[YEAR_START_INDEX_MOA:YEAR_END_INDEX_MOA])
				num_MOA = int(name_MOA[NUM_START_INDEX_MOA:])

#			if num_OGLE != None and num_OGLE > local_num_OGLE and year_OGLE != None and year_OGLE >= local_year_OGLE \
#			and num_MOA != None and num_MOA > local_num_MOA and year_MOA != None and year_MOA >= local_year_MOA:

			if num_OGLE != None and year_OGLE != None and num_MOA != None and year_MOA != None \
			and ((num_MOA > local_num_MOA and year_MOA >= local_year_MOA) or (num_OGLE > local_num_OGLE and year_OGLE >= local_year_OGLE)):		
			# exoFOP: has both OGLE and MOA numbers/years.			
			# Either: 
				# OGLE number is greater than stored OGLE number.
				# OGLE year is as or more recent than stored OGLE year.
			# OR:
				# MOA number is greater than stored MOA number.
				# MOA year is as or more recent than stored MOA year.")
				logger.debug("%s ? %s" % (num_OGLE, local_num_OGLE))
				logger.debug("%s ? %s" % (year_OGLE, local_year_OGLE))

				logger.debug("%s ? %s" % (num_MOA, local_num_MOA))
				logger.debug("%s ? %s" % (year_MOA, local_year_MOA))

				logger.debug("For at least one of the above num/year pairs, the comparison symbol should be >.")

				logger.info("New event found!")
				logger.info("Event: %s" % name_OGLE)
				logger.info("Event: %s" % name_MOA)
				logger.info("Both MOA and OGLE names found!")

				event = {"name_OGLE": name_OGLE, "name_MOA": name_MOA, "in_K2_footprint": in_K2_footprint, \
							  "in_K2_superstamp": in_K2_superstamp, "during_K2_campaign": during_K2_campaign}
				#ROGUE.evaluate_event(event)	
				events_to_evaluate.append(event)		
				logger.info("-------------------------------------")
			
			if num_OGLE == None and year_OGLE == None \
			 and num_MOA != None and num_MOA > local_num_MOA and year_MOA != None and year_MOA >= local_year_MOA:
				# exoFOP has: no OGLE number/year. But has MOA number/year.
				# MOA number is greater than stored MOA number.
				# MOA year is as or more recent than stored MOA year.

				logger.debug("%s > %s" % (num_MOA, local_num_MOA))
				logger.debug("%s > %s" % (year_MOA, local_year_MOA))

				logger.info("New event found!")
				logger.info("Event: %s" % name_MOA)
				logger.info("No OGLE name")

				event = {"name_MOA": name_MOA, "in_K2_footprint": in_K2_footprint, \
							  "in_K2_superstamp": in_K2_superstamp, "during_K2_campaign": during_K2_campaign}
				#ROGUE.evaluate_event(event)
				events_to_evaluate.append(event)
				logger.info("-------------------------------------")

			if num_MOA == None and year_MOA == None \
			 and num_OGLE > local_num_OGLE and year_OGLE != None and year_OGLE >= local_year_OGLE:
				# exoFOP has: no MOA number/year. But has OGLE number/year.
				# OGLE number is greater than stored OGLE number.
				# OGLE year is as or more recent than stored OGLE year.:
			
				logger.debug("%s > %s" % (num_OGLE, local_num_OGLE))
				logger.debug("%s > %s" % (year_OGLE, local_year_OGLE))

				logger.info("New event found!")
				logger.info("Event: %s" % name_OGLE)
				logger.info("No MOA name")
				event = {"name_OGLE": name_OGLE, "in_K2_footprint": in_K2_footprint, \
							  "in_K2_superstamp": in_K2_superstamp, "during_K2_campaign": during_K2_campaign}
				#ROGUE.evaluate_event(event)
				events_to_evaluate.append(event)
				logger.info("-------------------------------------")
	logger.info("Finished checking master list.")

	events_to_evaluate.sort()
	logger.debug("Events to evaluate:") 
	for event in events_to_evaluate:
		logger.debug(str(event))
	return events_to_evaluate

def test1():
	check_file = False
	input_filepath = "/science/robonet/rob/Operations/ExoFOP/master_events_list"
	output_filepath = os.path.join(sys.path[0], "readingMasterList_outputTest.txt")
	
	if check_file:
		newest_events_filepath = os.path.join(sys.path[0], "latest_events.txt")
		with open(newest_events_filepath, "r") as newest_event_file:
			newest_event_names = newest_event_file.read().split()
			newest_event_evaluated_OGLE = newest_event_names[0]
			newest_event_evaluated_MOA = newest_event_names[1]
	else:
		newest_event_evaluated_OGLE = "OGLE-2016-BLG-600"
		newest_event_evaluated_MOA = "MOA-2016-BLG-158"
	
	newest_events = {"OGLE": newest_event_evaluated_OGLE, "MOA": Newest_event_evaluatedMOA}
	check_event_master_list(newest_events)

def main():
	test1()

if __name__ == "__main__":
	main()
