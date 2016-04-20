"""
update_CSV.py
@author: Shanen Cross
"""
import sys
import os
import csv
import logging

import logger_setup

DEBUGGING_MODE = True

#LOG_DIR = os.path.join(sys.path[0], "logs/update_CSV_log")
LOG_DIR = "/science/robonet/rob/Operations/Logs/2016"
LOG_NAME = "update_CSV_log"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
if DEBUGGING_MODE:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on = True, console_output_level = "DEBUG")
else:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on = False, console_output_level = "DEBUG")

def update(file_output_path, new_dict, fieldnames, delimiter=","):
	# if csv file does NOT yet exist, open it for writing, sort the online events by name, and store each event dictionary
	# as a row in this sequence
	logger.info("-------------------------------------------------------------------------------------")
	if not os.path.isfile(file_output_path):
		logger.info("File does not exist. Opening file for writing...")
		with open(file_output_path, "w") as f:
			logger.info("File opened for writing.")
			logger.info("Writing file header...")
			writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
			writer.writeheader()
			new_name_list = sorted(new_dict)
			logger.debug("Sorted online events: " + str(new_name_list))
			logger.info("Writing to file...")
			for event_name in new_name_list:
				event_dict = new_dict[event_name]
				#logger.info("Writing dict to file: " + str(event_dict))
				writer.writerow(event_dict)

	# if file does already exist, read the existing file, get the sorted combined list of names from both online and locally stored events,
	# then write to file, storing each event dictionary from this combined list as a row in sequence. 
	# Store the updated online event dictionary when its available, else keep the local dictionary.
	else: 
		logger.info("File already exists. Opening file for reading...")
		with open(file_output_path, "r") as f:
			logger.info("File opened for reading.")
			reader = csv.DictReader(f, delimiter=delimiter)
			
			# get dictionary with names as keys and event dictionaries as values for locally stored events
			old_dict ={}
			for row in reader:
				if row.has_key("name_TAP") and row["name_TAP"] != "":
					nameKey = "name_TAP"

				elif row.has_key("name_OGLE") and row["name_OGLE"] != "":
					nameKey = "name_OGLE"

				elif row.has_key("name_MOA") and row["name_MOA"] != "":
					nameKey = "name_MOA"

				else:
					logger.warning("Error: Event row, " + str(row) + ", has no OGLE, MOA, or TAP name key.")
					nameKey = ""

				#logger.debug("Event row, " + str(row) + ", has name key: " +  str(nameKey))
				event_name = row[nameKey]
				#logger.debug("Event name: " + str(event_name))
				old_dict[event_name] = row
				#logger.debug("Stored event row " + str(row) + " in old dictionary with event name " + str(event_name) + " as key.")
				#logger.debug("Old dictionary: " + str(old_dict))

			logger.debug("Local events: " + str(old_dict))
			logger.debug("Online events: " + str(new_dict))
			# get set-like objects containing event names from local and online dictionaries,
			# then combine their set and sort it into an ordered list
			new_name_set = new_dict.viewkeys()
			old_name_set = old_dict.viewkeys()
			combined_name_list = sorted(new_name_set | old_name_set)
			logger.debug("Old name set: " + str(old_name_set))
			logger.debug("New name set: " + str(new_name_set))
			logger.debug("Combined name set: " + str(new_name_set | old_name_set))
			logger.debug("Sorted Combined name list: " + str(combined_name_list))
		logger.info("File read.")
		logger.info("Opening file for writing...")
		with open(file_output_path, "w") as f:
			logger.info("File opened for writing.")
			logger.debug("Sorted combined name list: " + str(combined_name_list))
			logger.debug("Writing file header...")
			writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
			writer.writeheader()
			logger.info("Writing to file...")
			# Get and write the event dictionary for each event from the combined list in sequence. 
			# If available, get the online event. Otherwise, get the locally stored event.
			for name in combined_name_list:
				if name in new_name_set:
					event_dict = new_dict[name]
				elif name in old_name_set:
					event_dict = old_dict[name]
				else:
					logger.warning("Error: Somehow the name %s in the combined list %s is not in either the local (%s) or online (%s) name sets." % \
						  (name, combined_name_list, old_name_set, new_name_set))
					event_dict = None
				logger.debug("Writing event dictionary: " + str(event_dict))
				writer.writerow(event_dict)
		logger.info("File written.")
	logger.info("-------------------------------------------------------------------------------------")

def main():
	pass

if __name__ == "__main__":
	main()
