"""
ROGUE.py
IN-USE ACTIVE COPY
Purpose: Poll MOA (and eventually OGLE) website for microlensing events, checking for ones likely to 
indicate rogue planets or planets distant from their parent star
Author: Shanen Cross
Date: 2016-03-31
"""
"""
Note: Does not currently account for corresponding MOA and OGLE events possibly having different years.
For instance, some 2016 MOA events have 2015 OGLE counterparts.
This script will detect no OGLE counterpart for such a MOA event.
It will also ignore any MOA event prior to the current year, regardless of whether its OGLE
counterpart are listed in the current year.
"""
import sys # for getting script directory
import os # for file-handling
import logging
import requests # for fetching webpages
from bs4 import BeautifulSoup # html parsing dates
from datetime import datetime # for getting current year for directories and URLs
from K2fov.c9 import inMicrolensRegion # K2 tool for checking if given RA and Dec coordinates are in K2 Campaign 9 microlensing region

# local script imports
import logger_setup # setting up logger
import reading_master_list
from data_collection_and_output import event_data_collection # collecting data from survey sites and ARTEMIS,
														# as well as outputting HTML summary page and event trigger record .csv
import update_CSV
import event_tables_comparison
import mail_notification # script for sending emails by executing command line tool

requests.packages.urllib3.disable_warnings() # to disable warnings when accessing insecure sites

DEBUGGING_MODE = True # Turn this flag on if modifying and testing code - turn it off when actively being used

# create and set up filepath and directory for logs -
# log dir is subdir of script
LOG_DIR = os.path.join(sys.path[0], "logs/ROGUE_log")
LOG_NAME = "ROGUE_log"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
if DEBUGGING_MODE:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=True, console_output_level = "DEBUG")
else:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=False, console_output_level = "DEBUG")

# set up filepath and directory for local copy of newest microlensing event
LOCAL_EVENTS_FILENAME = "last_event.txt"
LOCAL_EVENTS_DIR = os.path.join(sys.path[0], "last_event")
LOCAL_EVENTS_FILEPATH = os.path.join(LOCAL_EVENTS_DIR, LOCAL_EVENTS_FILENAME)
if not os.path.exists(LOCAL_EVENTS_DIR):
	os.makedirs(LOCAL_EVENTS_DIR)

# Set up filepath for .csv file of TAP event triggers
TAP_DIR = os.path.join(sys.path[0], "TAP_target_table")
TAP_FILENAME = "TAP_target_table.csv"
TAP_FILEPATH = os.path.join(TAP_DIR, TAP_FILENAME)

# Set up filepath for ROGUE vs. TAP comparison table HTML file
COMPARISON_TABLE_DIR = os.path.join(sys.path[0], "comparison_table")
COMPARISON_TABLE_FILENAME = "ROGUE_vs_TAP_Comparison_Table.html"
COMPARISON_TABLE_FILEPATH = os.path.join(COMPARISON_TABLE_DIR, COMPARISON_TABLE_FILENAME)
if not os.path.exists(COMPARISON_TABLE_DIR):
	os.makedirs(COMPARISON_TABLE_DIR)

if DEBUGGING_MODE:
	CURRENT_YEAR = "2016" #TEMPORARY FOR TESTING/DEBUGGING - CHANGE TO LINE BELOW
else:
	# set year as constant using current date/time, for accessing URLs
	CURRENT_YEAR = str(datetime.utcnow().year)

# setup URL paths for website event index and individual pages
WEBSITE_URL = "https://it019909.massey.ac.nz/moa/alert" + CURRENT_YEAR + "/"
INDEX_URL_DIR= "/index.dat"
INDEX_URL = WEBSITE_URL + INDEX_URL_DIR
EVENT_PAGE_URL_DIR = "/display.php?id=" #event page URL path is this with id number attached to end

LOCAL_EVENT_OGLE_INDEX = 0
LOCAL_EVENT_MOA_INDEX = 1

# column numbers for event ID, Einstein time and baseline magnitude
# for index.dat file (zero-based counting)
NAME_INDEX = 0
ID_INDEX = 1
RA_INDEX = 2
DEC_INDEX = 3
TMAX_INDEX = 4
TIME_INDEX = 5
U0_INDEX = 6
BASELINE_MAG_INDEX = 7

MAX_EINSTEIN_TIME = 10 # days - only check events as short or shorter than this
MIN_MAG = 17.5 # magnitude units - only check events as bright or brighter than this
			   # (i.e. numerically more negative values)
MAX_MAG_ERR = 0.7 # magnitude units - maximum error allowed for a mag
EINSTEIN_TIME_ERROR_NOTIFICATION_THRESHOLD = 1 # days - if Einstein Time error is less than this, email is labeled "Event Notification"; 
										# otherwise email is labeled "Event Warning"

EVENT_TRIGGER_RECORD_DIR = os.path.join(sys.path[0], "event_trigger_record")
EVENT_TRIGGER_RECORD_FILENAME = "event_trigger_record.csv"
EVENT_TRIGGER_RECORD_FILEPATH = os.path.join(EVENT_TRIGGER_RECORD_DIR, EVENT_TRIGGER_RECORD_FILENAME)
if not os.path.exists(EVENT_TRIGGER_RECORD_DIR):
	os.makedirs(EVENT_TRIGGER_RECORD_DIR)

# Fieldnames and delimiter for .csv file storing event triggers
FIELDNAMES = ["name_MOA", "name_OGLE", "ID_MOA", "RA_MOA", "Dec_MOA", "tE_MOA", "tE_err_MOA", "RA_OGLE", \
			  "Dec_OGLE", "tE_OGLE", "tE_err_OGLE", "tE_ARTEMIS_MOA", "tE_err_ARTEMIS_MOA", "tE_ARTEMIS_OGLE", \
			  "tE_err_ARTEMIS_OGLE", "u0_MOA", "u0_err_MOA", "u0_OGLE", "u0_err_OGLE", "u0_ARTEMIS_MOA", \
			  "u0_err_ARTEMIS_MOA", "u0_ARTEMIS_OGLE", "u0_err_ARTEMIS_OGLE", "mag_MOA", "mag_err_MOA"]

DELIMITER = ","


"""
#List of tests we will use to determine whether to send out notifications for an event.
#Any tests omitted will still be run and recorded, but will not affect whether mail notifications
#are sent out.
#Possible criteria: tE, microlensing_assessment_MOA, microlensing_region, mag
CRITERIA = ["tE"]

# Dictionary showing what
TESTS =
"""

# Flag for mail notifications functionality and list of mailing addresses
if DEBUGGING_MODE:
	MAIL_NOTIFICATIONS_ON = True
	SUMMARY_BUILDER_ON = True
	EVENT_TRIGGER_RECORD_ON = True
	EVENT_TABLE_COMPARISON_ON = True
	MAILING_LIST = ["shanencross@gmail.com"]

else:
	MAIL_NOTIFICATIONS_ON = True
	SUMMARY_BUILDER_ON = True
	EVENT_TRIGGER_RECORD_ON = True
	EVENT_TABLE_COMPARISON_ON = True
	MAILING_LIST = ["shanencross@gmail.com"]
	#MAILING_LIST = ["shanencross@gmail.com", "rstreet@lcogt.net", "calen.b.henderson@gmail.com", \
	#				"yossishv@gmail.com", "robonet-ops@lcogt.net"]

# Global dictionary of event triggers to update .csv file with
event_trigger_dict = {}

def run_ROGUE():
	logger.info("---------------------------------------")
	logger.info("Starting program")
	logger.info("Storing newest events in: " + LOCAL_EVENTS_FILEPATH)
	logger.info("Max Einstein Time allowed: " + str(MAX_EINSTEIN_TIME) + " days")
	logger.info("Dimmest magnitude allowed: " + str(MIN_MAG))
	logger.info("Max magnitude error allowed: " + str(MAX_MAG_ERR))

	local_events = get_local_events(LOCAL_EVENTS_FILEPATH)
	events_to_evaluate = reading_master_list.check_event_master_list(local_events)
	
	for event in events_to_evaluate:
		evaluate_event(event)

	save_and_compare_triggers()
	logger.debug(str(event_trigger_dict))
	logger.info("Ending program")
	logger.info("---------------------------------------")

def get_local_events(filepath):
	logger.info("Obtaining most recent MOA and OGLE events...")
	if not os.path.exists(filepath):
		logger.warning("File containing most recent MOA and OGLE events not found at %s." % (filepath)) 
		return None

	with open(filepath, "r") as events_file:
		events_split = events_file.read().split()
		event_name_OGLE = events_split[LOCAL_EVENT_OGLE_INDEX]
		event_name_MOA = events_split[LOCAL_EVENT_MOA_INDEX]
		
		events_dict = {"OGLE": event_name_OGLE, "MOA": event_name_MOA}

	return events_dict

def evaluate_event(event):
	"""Evaluate whether event is short enough to potentially indicate a rogue planet
	and whether it is bright enough to be worth further observation.
	"""
	logger.info("")
	logger.info("Event Evaluation:")

	# place relevant values from event row in MOA table into dictionary as strings for ease of access
	try:
		updated_event = event_data_collection.collect_data(event)
	except Exception as ex:
		logger.warning("Exception collecting data from survey site(s) and/or ARTEMIS")
		logger.warning(ex)
		return

	sources = []
	if updated_event.has_key("name_OGLE"):
		sources.append("OGLE")
	if updated_event.has_key("name_ARTEMIS_OGLE"):
		sources.append("ARTEMIS_OGLE")
	if updated_event.has_key("name_ARTEMIS_MOA"):
		sources.append("ARTEMIS_MOA")
	if updated_event.has_key("name_MOA"):
		sources.append("MOA")

	evaluate_event_data(updated_event, sources=sources)
	# evaluate Einstein time, microlensing vs. cv status, and magnitude
	# for whether to trigger observation
	#evaluate_event_page_MOA(values_MOA)

def evaluate_event_data(event, sources=["OGLE"]):
	"""Evaluate event using information from the survey event page or ARTEMIS file."""

	trigger_this_event = False
	tE_test = "untested"
	microlensing_assessment_test = "untested"
	microlensing_region_test = "untested" # Checking exoFPO master event list for K2 superstamp
	microlensing_region_alternate_test = "untested" # Testing for K2 superstamp ourselves, with K2fov module
	mag_test = "untested"
	
	assessment_MOA = ""
	for source in sources:
		# Run Einstein time test
		tE_key = "tE_" + source
		tE_err_key = "tE_err_" + source
		tE = event[tE_key]
		tE_err = event[tE_err_key]

		logger.info("For fit from source %s:" % (source))
		einstein_time_check = check_einstein_time(tE, tE_err)
		if einstein_time_check:
			logger.info("%s Einstein time passed!" % source)
			tE_test = "passed"
			if event.has_key("passing_tE_sources"):
				event["passing_tE_sources"].append(source)
			else:
				event["passing_tE_sources"] = [source]
		else:
			logger.info("%s Einstein time failed: lower bound must be equal to or less than %s days." % (source, str(MAX_EINSTEIN_TIME)))
			if tE_test == "untested":			
				tE_test = "failed"		

		# Run tests which only apply to MOA events
		if source == "MOA":
			# Run MOA microlensing assessment test
			assessment_MOA = event["assessment_MOA"]

			# Run MOA most-recent-magnitude-without-too-large-of-an-error test
			mag_values = [event[mag_MOA], event[mag_MOA_err]]
			if check_mag(mag_values):
				mag_test = "passed"
			else:
				mag_test = "failed"

			#DEBUG: Run alternate K2 microlensing superstamp testing
			# For testing agreement with two methods of testing K2 superstamp
			if DEBUGGING_MODE:
				RA_degrees_MOA = event["RA_degrees_MOA"]
				Dec_degrees_MOA = event["Dec_degrees_MOA"]
				if check_microlens_region(RA_degrees_MOA, Dec_degrees_MOA):
					microlensing_region_alternate_test = "passed"
				else:
					microlensing_region_alternate_test = "failed"

	if event.has_key("passing_tE_sources"):
		event["passing_tE_sources"].sort()
		passing_tE_sources = event["passing_tE_sources"]
		passing_tE_sources_output = "Passing tE sources: "
		for i in xrange(len(passing_tE_sources)):
			passing_tE_sources_output += passing_tE_sources[i]
			if i < len(passing_tE_sources) - 1:
				passing_tE_sources_output += ", "
		logger.debug(passing_tE_sources_output)

	if assessment_MOA != "":
		if is_microlensing(assessment_MOA):
			microlensing_assessment_test = "passed"
		else:
			microlensing_assessment_test = "failed"

	if event.has_key("in_K2_superstamp"):
		if event["in_K2_superstamp"]:
			microlensing_region_test = "passed"
		else:
			microlensing_region_test = "failed"
	
	#DEBUG: Testing agreement with using K2 superstamp test ourselves, instead of relying on master list
	if DEBUGGING_MODE:
		if microlensing_region_test != microlensing_region_alternate_test:
			logger.warning("There is disagreement about the test for whether the event is in the K2 superstamp.")
			logger.warning("The test which uses the K2fov module, evaluating the RA and Dec from MOA, says that the event:")
			if microlensing_region_alternate_test == "passed":
				logger.warning("passes.")
			elif microlensing_region_alternate_test == "failed":
				logger.warning("does NOT pass.")
			elif microlensing_region_alternate_test == "untested":
				logger.warning("was not tested.")
			logger.warning("The exoFOP master event list test says that the event:")
			if microlensing_region_test == "passed":
				logger.warning("passes.")
			elif microlensing_region_test == "failed":
				logger.warning("does NOT pass.")	
				logger.warning("This means the superstamp entry in the master list is either False or Unknown.")
			elif microlensing_region_test == "untested":
				logger.warning("was not tested.")

	# Add test results to event dictionary
	event["tE_test"] = tE_test
	event["microlensing_assessment_test"] = microlensing_assessment_test
	event["microlensing_region_test"] = microlensing_region_test
	if DEBUGGING_MODE:
		event["microlensing_region_alternate_test"] = microlensing_region_alternate_test
	event["mag_test"] = mag_test

	# Turn on trigger flag if the tE test was successful - 
	# we can change the criteria for activating the trigger flag if we'd like
	if tE_test == "passed":
		trigger_this_event = True

	# Trigger if trigger flag is on
	if trigger_this_event:
		trigger_event(event)

def trigger_event(event):
	"""Runs when an event fits our criteria. Triggers mail notifications and builds summary if those flags are on."""

	logger.info("Event is potentially suitable for observation!")
	if MAIL_NOTIFICATIONS_ON:
		logger.info("Mailing event notification...")
		try:
			send_mail_notification(event)
		except Exception as ex:
			logger.warning("Exception attempting to mail event notification")
			logger.warning(ex)

	if SUMMARY_BUILDER_ON:
		logger.info("Building and outputting event summary page...")
		try:
			event_data_collection.build_summary(event)
		except Exception as ex:
			logger.warning("Exception building/outputting event summary")
			logger.warning(ex)

	if EVENT_TRIGGER_RECORD_ON:
		logger.info("Saving event dictionary to dictionary of event dictionaries, to be outputted later...")
		try:
			add_event_to_trigger_dict(event)
		except Exception as ex:
			logger.warning("Exception converting event data dictionary format and/or saving event to event trigger dictionary.")
			logger.warning(ex)

def check_einstein_time(tE_string, tE_err_string=None):
	"""Check if Einstein time is short enough for observation."""
	einstein_time = float(tE_string)
	logger.info("Einstein Time: " + str(einstein_time) + " days")

	if tE_err_string != None and tE_err_string != "":
		einstein_time_err = float(tE_err_string)
		logger.info("Einstein Time Error: " + str(einstein_time_err) + " days")

		einstein_time_lower_bound = einstein_time - einstein_time_err
		logger.info("Einstein Time Lower Bound = %s - %s = %s days" % (str(einstein_time), str(einstein_time_err), \
																	   str(einstein_time_lower_bound)))

	else:
		logger.info("No error given for Einstein time. Using given Einstein Time value as lower bound " + \
					"for comparison with max Einstein Time threshold.")
		einstein_time_lower_bound = einstein_time
		logger.info("Einstein Time Lower Bound = %s days" % str(einstein_time_lower_bound))

	einstein_time_check = (einstein_time_lower_bound <= MAX_EINSTEIN_TIME)

	return einstein_time_check

def get_einstein_time_err_MOA(event_page_soup):
	"""Return string of Einstein Time error from event page soup."""

	micro_table = event_page_soup.find(id="micro").find_all('tr')
	tE_err = float(micro_table[1].find_all('td')[4].string.split()[0])
	return str(tE_err)

def check_microlens_region(RA_string, Dec_string):
	"""Check if strings RA and Dec coordinates are within K2 Campaign 9 microlensing region (units: degrees)."""
	# Convert strings to floats and output to logger
	RA = float(RA_string)
	Dec = float(Dec_string)
	logger.info("RA: " + str(RA) + "      Dec: " + str(Dec) + "      (Units: Degrees)")

	# pass to K2fov.c9 module method (from the K2 tools) to get whether coordinates are in the region
	return in_microlens_region(RA, Dec)

def get_event_page_soup_MOA(values_MOA):
	"""Return event page Soup from inital MOA values (must contain MOA ID at least). 
	   Also add event page URL to values dictionary parameter."""

	event_page_URL = WEBSITE_URL + EVENT_PAGE_URL_DIR + values_MOA["ID"]
	values_MOA["pageURL"] = event_page_URL
	event_page_soup = BeautifulSoup(requests.get(event_page_URL, verify=False).content, 'lxml')
	return event_page_soup

def is_microlensing(assessment):
	"""Check if event is microlensing, cv, a combination of the two, or unknown -
    Should this return true or false if event is "microlensing/cv" (currently returns true)?
	"""
	logger.info("Current assessment: " + assessment)
	if assessment == "microlensing" or assessment == "microlensing/cv":
		return True
	else:
		return False

def check_mag(mag_values):
	"""Check if magnitude is bright enough for observation."""
	# logger.debug("Returned mag array: " + str(mag_values))
	# if no magnitudes were found
	if mag_values is None:
		logger.info("Magnitude: None found")
		return False
	mag = mag_values[0]
	mag_err = mag_values[1]
	#mag_err_too_large = mag_values[2]
	mag_err_too_large = (mag_err > MAX_MAG_ERR)
	logger.info("Magnitude: " + str(mag))
	logger.info("Magnitude error: " + str(mag_err))

	# more negative mags are brighter, so we want values less than
	# our minimum brightness magnitude	
	if mag > MIN_MAG or mag_err_too_large:
		return False
	else:
		return True

def add_event_to_trigger_dict(event):
	"""Add event data dictionary (dictionary containing separate dictionaries for data from each survey) \
	to dictionary of event triggers, first converting it to a single event dictionary containing items from all surveys."""

	converted_event = convert_event_for_output(event)

	# Use OGLE name for key pointing to event as value if availble.
	if converted_event.has_key("name_OGLE") and converted_event["name_OGLE"] != "":
		logger.info("Event has OGLE name")
		name_key = "name_OGLE"

	# Otherwise, use the MOA name.
	elif converted_event.has_key("name_MOA") and converted_event["name_MOA"] != "":
		logger.info("Event has MOA name and no OGLE name")
		name_key = "name_MOA"

	# If there is a neither a MOA nor OGLE name, something has gone wrong, and we abort storing the event.
	else:
		logger.warning("Event has neither OGLE nor MOA name item. Event:\n" + str(converted_event))
		logger.warning("Aborting added event to event trigger dictionary...")
		return

	event_name = converted_event[name_key]
	global event_trigger_dict
	event_trigger_dict[event_name] = converted_event
	logger.debug(str(event_trigger_dict))

def convert_event_for_output(event):
	"""Return a copy of event dictionary which has all elements removed
	except those with keys specified by the FIELDNAMES list,
	which indicates which fields are to be included in .csv record of
	event triggers."""

	converted_event = {}	
	for fieldname in FIELDNAMES:
		if event.has_key(fieldname):
			converted_event[fieldname] = event[fieldname]

	return converted_event

def save_and_compare_triggers():
	if EVENT_TRIGGER_RECORD_ON:
		logger.info("Outputting event to .csv record of event triggers...")
		try:
			update_CSV.update(EVENT_TRIGGER_RECORD_FILEPATH, event_trigger_dict, fieldnames=FIELDNAMES, delimiter=DELIMITER)
		except Exception as ex:
			logger.warning("Exception outputting .csv record of event triggers")
			logger.warning(ex)
			return

		if EVENT_TABLE_COMPARISON_ON:
			logger.info("Generating and outputting HTML page with comparison table of ROGUE and TAP event triggers...")
			try:
				event_tables_comparison.compare_and_output(EVENT_TRIGGER_RECORD_FILEPATH, TAP_FILEPATH, COMPARISON_TABLE_FILEPATH)
			except Exception as ex:
				logger.warning("Exception generating/outputting comparison table HTML page")
				logger.warning(ex)		

def get_notification_level_and_message(event):
	"""Return notification level as "Warning" or "notification" and related message depending on whether tE error exceeds our threshold constant""" 

	if not event.has_key("passing_tE_sources"):
		logger.warning("This event has no recorded passing tE sources (i.e. MOA, OGLE, ARTEMIS_MOA, or ARTEMIS_OGLE).")
		logger.warning("Cannot discern mail notification level or generate notification level message.")

	notification_level = "Warning"
	for source in event["passing_tE_sources"]:
		tE_err_key = "tE_err_" + source
		tE_err = float(event[tE_err_key])
		if tE_err <= EINSTEIN_TIME_ERROR_NOTIFICATION_THRESHOLD:
			notification_level = "Alert"

	message = "Because"
	if notification_level == "Warning":
		message += " at least one of the Einstein Times that passed our criteria has an error smaller than"
	elif notification_level == "Alert":
		message += " none of the Einstein Times that passed our criteria have an error greater than"

	message += " an error threshold of " + str(EINSTEIN_TIME_ERROR_NOTIFICATION_THRESHOLD)
	message += " day(s), this email has been given the status of \"Event %s\"." % str(notification_level)
	notification_dict = {"notification level": notification_level, "message": message}
	logger.info("Event notification level: Event " + str(notification_dict["notification level"]))
	
	return notification_dict

def send_mail_notification(event):
	"""Send mail notification upon detecting short duration microlensing event"""
	"""
	if DEBUGGING_MODE:
		notification_level = "Warning"
		notification_level_message = ""
	else:
		notification_level_dict = get_notification_level_and_message(event)
		notification_level = notification_level_dict["notification level"]
		notification_level_message = notification_level_dict["message"]
	"""
	notification_level_dict = get_notification_level_and_message(event)
	notification_level = notification_level_dict["notification level"]
	notification_level_message = notification_level_dict["message"]	

	message_text = \
"""\
Potential Short Duration Microlensing Event %s
%s

""" % (notification_level, notification_level_message)

	if event.has_key("name_OGLE"):
		message_text += \
"""\
OGLE Event Name: %s
OGLE Einstein Time: %s +/- %s
OGLE Event Page: %s

""" % ( event["name_OGLE"], event["tE_OGLE"], event["tE_err_OGLE"], event["pageURL_OGLE"])

	if event.has_key("name_MOA"):
		message_text += \
"""\
MOA Event Name: %s
MOA Event ID: %s
MOA Einstein Time: %s +/- %s
MOA Event Page: %s

""" % ( event["name_MOA"], event["ID_MOA"], event["tE_MOA"], event["tE_err_MOA"], event["pageURL_MOA"])

	# The name used for reference, in the subject and summary page URL, is the OGLE event if available
	# Otherwise it is the MOA name
	if event.has_key("name_OGLE"):
		reference_event_name = event["name_OGLE"]
	elif event.has_key("name_MOA"):
		reference_event_name = event["name_MOA"]
	else:
		logger.warning("Event has neither MOA nor OGLE name.")
		logger.warning("Canceling mail notification.")
		return
	
	if event.has_key("name_ARTEMIS_OGLE"):
		message_text += \
"""\
ARTEMIS OGLE Event Name: %s
ARTEMIS OGLE Einstein Time: %s +/- %s

""" % ( event["name_ARTEMIS_OGLE"], event["tE_ARTEMIS_OGLE"], event["tE_err_ARTEMIS_OGLE"])

	if event.has_key("name_ARTEMIS_MOA"):
		message_text += \
"""\
ARTEMIS MOA Event Name: %s
ARTEMIS MOA Einstein Time: %s +/- %s

""" % ( event["name_ARTEMIS_MOA"], event["tE_ARTEMIS_MOA"], event["tE_err_ARTEMIS_MOIA"])

	mail_subject = reference_event_name + " - Potential Short Duration Microlensing Event " + str(notification_level)
	summary_page_URL = "http://robonet.lcogt.net/robonetonly/WWWLogs/eventSummaryPages/" + reference_event_name + "_summary.html"
	message_text += \
"""\
Event summary page: %s 

""" % (summary_page_URL)

	if DEBUGGING_MODE:
		tests = ["tE_test", "microlensing_assessment_test", "microlensing_region_test", "microlensing_region_alternate_test", "mag_test"]
	else:
		tests = ["tE_test", "microlensing_assessment_test", "microlensing_region_test", "mag_test"]

	message_text += \
"""\
Tests:
"""
	for test in tests:
		if event.has_key(test):
			message_text += \
"""\
%s status: %s
""" % (test, event[test])
		
	mail_notification.send_notification(message_text, mail_subject, MAILING_LIST)
	logger.debug(message_text)
	logger.info("Event notification mailed!")

def main():
	run_ROGUE()

if __name__ == "__main__":
	main()
