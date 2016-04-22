"""
TAP_table_recording.py
IN-PROGRESS WORKING COPY
Purpose: Download Markus and update TAP Kepler Short Candidate List from the the robonet server, then compare to stored list of event triggers from webpageAcesss.py
@author: Shanen Cross
Date: 2016-03-18
"""
import os
import sys
import requests
import csv
from bs4 import BeautifulSoup
import logging

import logger_setup
import update_CSV

DEBUGGING_MODE = True

# Set up logger
#LOG_DIR = os.path.join(sys.path[0], "logs/TAP_table_recording_log")
LOG_DIR = "/science/robonet/rob/Operations/Logs/2016"
LOG_NAME = "TAP_table_recording_log"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
if DEBUGGING_MODE:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=True, console_output_level = "DEBUG")
else:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=False, console_output_level = "DEBUG")

# local script imports
#from compareEventTables import compareEvents
#from dataCollectionAndOutput import collectEventData

FILENAME = "target_list_comparison.txt"
TAP_TARGET_TABLE_URL = "http://robonet.lcogt.net/temp/tap1mlist_kepler_short.html"
TEST_TAP_TARGET_TABLE_FILEPATH = "/home/scross/Documents/Workspace/RoguePlanetMicrolensingProject/webpageAccess/testing/shortTargetTableComparison/TAP_test.html"
online_TAP_events = {}

# set up and create ouptut directory and filename for TAP target table
TAP_TARGET_TABLE_OUTPUT_FILENAME = "TAP_target_table.csv"
TAP_TARGET_TABLE_OUTPUT_DIR = os.path.join(sys.path[0], "TAP_target_table")
TAP_TARGET_TABLE_OUTPUT_FILEPATH = os.path.join(TAP_TARGET_TABLE_OUTPUT_DIR, TAP_TARGET_TABLE_OUTPUT_FILENAME)
if not os.path.exists(TAP_TARGET_TABLE_OUTPUT_DIR):
	os.makedirs(TAP_TARGET_TABLE_OUTPUT_DIR)

LOCAL_TEST_ONLY = False

def update_table():

	#print "Updating table."
	# Load local HTML file as TAP Target webpage if testing the script. 
	# If running the script for real, access the online TAP target page.
	if LOCAL_TEST_ONLY:
		logger.info("Running test with local file for TAP target table...")
		logger.info("Opening local page %s..." % (TEST_TAP_TARGET_TABLE_FILEPATH))
		#print "This is a local test. Opening local page %s..." % (TEST_TAP_TARGET_TABLE_FILEPATH)
		with open(TEST_TAP_TARGET_TABLE_FILEPATH, 'r') as pageFile:
			logger.info("File opened.")
			target_list_soup = BeautifulSoup(pageFile, "lxml") 
	else:
		logger.info("This is not a local test. Opening online page %s..." % (TAP_TARGET_TABLE_URL))
		target_list_soup = BeautifulSoup(requests.get(TAP_TARGET_TABLE_URL, verify=False).content, "lxml")

	logger.debug("Page soup acquired:\n" + target_list_soup.prettify())

	# Navigate to the webpage's event table with Beautiful Soup
	events = target_list_soup.find("table").find_all("tr")[1:]
	global online_TAP_events
	online_TAP_events = {} #empty list in case it was filled previously

	# Collect data from webpage soup
	for event in events:
		#print "Working on line:\n" + event.prettify()

		event_lines = event.find_all("td")
		event_name = event_lines[0].string
		event_RA = event_lines[2].string
		event_Dec = event_lines[3].string
		event_exposure_time = event_lines[6].string
		event_priority = event_lines[7].string
		event_mag = event_lines[9].string
		event_tE = event_lines[15].string
		event_tE_err = event_lines[16].string
		
		# Store data as a dictionary of dictionaries. The inner dictionaries are the "events", 
		# containing items for each piece of data about the events.
		# The outer dictionary uses event names as keys, each pointing to an event dictionary as a value.
		event_dict = {"name_TAP": event_name, "RA_TAP": event_RA, "Dec_TAP": event_Dec, \
					  "exposureTime_TAP": event_exposure_time, "priority_TAP": event_priority, \
					  "mag_TAP": event_mag, "tE_TAP": event_tE, "tE_err_TAP": event_tE_err}
		online_TAP_events[event_name] = event_dict
		logger.debug("Obtained event dictionary: %s" % (str(event_dict)))
	#print "Obtained online TAP table: %s" % (str(online_TAP_events))

def print_online_table():
	TAP_name_list = sorted(online_TAP_events)
	for event_name in TAP_name_list:
		event_dict = online_TAP_events[event_name]
		for item in event_dict:
			print item + ": " + event_dict[item]
		print

def save_table():
	# Column field names for table
	fieldnames = ["name_TAP","RA_TAP", "Dec_TAP", "priority_TAP", "mag_TAP", "tE_TAP", "tE_err_TAP", "exposureTime_TAP"]
	delimiter = ","
	logger.info("Update .csv file with events using update_CSV script...")
	update_CSV.update(TAP_TARGET_TABLE_OUTPUT_FILEPATH, online_TAP_events, fieldnames=fieldnames, delimiter=delimiter)
	
	"""
	# if csv file does NOT yet exist, open it for writing, sort the online TAP events by name, and store each event dictionary
	# as a row in this sequence
	if not os.path.isfile(TAP_TARGET_TABLE_OUTPUT_FILEPATH):
		#print "File does not exist. Opening file for writing..."
		with open(TAP_TARGET_TABLE_OUTPUT_FILEPATH, "w") as f:
			#print "File opened for writing."
			writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
			writer.writeheader()
			onlineTAPname_list = sorted(online_TAP_events)
			#print "Sorted online TAP events: " + str(onlineTAPname_list)
			for event_name in onlineTAPname_list:
				event_dict = online_TAP_events[event_name]
				#print "Writing dict to file: " + str(event_dict)
				writer.writerow(event_dict)

	# if file does already exist, read the existing file, get the sorted combined list of names from both online and locally stored events,
	# then write to file, storing each event dictionary from this combined list as a row in sequence. 
	# Store the updated online event dictionary when its available, else keep the local dictionary.
	else: 
		#print "File already exists. Opening file for reading..."
		with open(TAP_TARGET_TABLE_OUTPUT_FILEPATH, "r") as f:
			#print "File opened for reading."
			reader = csv.DictReader(f, delimiter=delimiter)
			
			# get dictionary with names as keys and event dictionaries as values for locally stored events
			localTAPevents ={}
			for row in reader:
				event_name = row["name_TAP"]
				localTAPevents[event_name] = row		

			#print "Local TAP events: " + str(localTAPevents)
			#print "Online TAP events: " + str(online_TAP_events)
			# get set-like objects containing event names from local and online dictionaries,
			# then combine their set and sort it into an ordered list
			onlineTAPname_set = online_TAP_events.viewkeys()
			localTAPname_set = localTAPevents.viewkeys()
			combinedTAPname_list = sorted(onlineTAPname_set | localTAPname_set)
			#print "combined set: " + str(onlineTAPname_set | localTAPname_set)
			#print "combined TAP name list: " + str(combinedTAPname_list)

		#print "Opening file for writing..."
		with open(TAP_TARGET_TABLE_OUTPUT_FILEPATH, "w") as f:
			#print "File opened for writing."
			#print "combined TAP name list: " + str(combinedTAPname_list)
			writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
			writer.writeheader()

			# Get and write the event dictionary for each event from the combined list in sequence. 
			# If available, get the online event. Otherwise, get the locally stored event.
			for name in combinedTAPname_list:
				if name in onlineTAPname_set:
					event_dict = online_TAP_events[name]
				elif name in localTAPname_set:
					event_dict = localTAPevents[name]
				else:
					print "Error: Somehow the name %s in the combined list %s is not in either the local (%s) or online (%s) name sets." % \
						  (name, combinedTAPname_list, localTAPname_set, onlineTAPname_set)
					event_dict = None
				#print "Writing event dictionary: " + str(event_dict)
				writer.writerow(event_dict)
		"""
def update_and_save_table():
	logger.info("------------------------------------------------------------------------------")
	update_table()
	save_table()
	logger.info("------------------------------------------------------------------------------")

def main():
	update_and_save_table()	
	"""
	update_table()
	#print_online_table()
	#print "Online TAP events: " + str(online_TAP_events)
	save_table()
	"""

if __name__== "__main__":
	main()
