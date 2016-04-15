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
import mail_alert # script for sending emails by executing command line tool

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
TAP_DIR = os.path.join(sys.path[0], "TAPtargetTable")
TAP_FILENAME = "TAPtargetTable.csv"
TAP_FILEPATH = os.path.join(TAP_DIR, TAP_FILENAME)

# Set up filepath for ROGUE vs. TAP comparison table HTML file
COMPARISON_TABLE_DIR = os.path.join(sys.path[0], "comparisonTable")
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

MAX_EINSTEIN_TIME = 3 # days - only check events as short or shorter than this
MIN_MAG = 17.5 # magnitude units - only check events as bright or brighter than this
			   # (i.e. numerically more negative values)
MAX_MAG_ERR = 0.7 # magnitude units - maximum error allowed for a mag
EINSTEIN_TIME_ERROR_ALERT_THRESHOLD = 1 # days - if Einstein Time error is less than this, email is labeled "Event Alert"; 
										# otherwise email is labeled "Event Warning"

EVENT_TRIGGER_RECORD_DIR = os.path.join(sys.path[0], "eventTriggerRecord")
EVENT_TRIGGER_RECORD_FILENAME = "eventTriggerRecord.csv"
EVENT_TRIGGER_RECORD_FILEPATH = os.path.join(EVENT_TRIGGER_RECORD_DIR, EVENT_TRIGGER_RECORD_FILENAME)
if not os.path.exists(EVENT_TRIGGER_RECORD_DIR):
	os.makedirs(EVENT_TRIGGER_RECORD_DIR)

# Fieldnames and delimiter for .csv file storing event triggers
FIELDNAMES = ["name_MOA", "name_OGLE", "ID_MOA", "RA_MOA", "Dec_MOA", "tE_MOA", "tE_err_MOA", "tE_OGLE", "tE_err_OGLE", "tE_ARTEMIS_MOA", "tE_err_ARTEMIS_MOA", \
			  "tE_ARTEMIS_OGLE", "tE_err_ARTEMIS_OGLE", "u0_MOA", "u0_err_MOA", "u0_OGLE", "u0_err_OGLE", "u0_ARTEMIS_MOA", "u0_err_ARTEMIS_MOA", \
			  "u0_ARTEMIS_OGLE", "u0_err_ARTEMIS_OGLE", "mag_MOA", "mag_err_MOA"]

DELIMITER = ","

# Flag for mail alerts functionality and list of mailing addresses
if DEBUGGING_MODE:
	MAIL_ALERTS_ON = True
	SUMMARY_BUILDER_ON = True
	EVENT_TRIGGER_RECORD_ON = True
	EVENT_TABLE_COMPARISON_ON = True
	MAILING_LIST = ["shanencross@gmail.com"]

else:
	MAIL_ALERTS_ON = True
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
	reading_master_list.check_event_master_list(local_events)

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


	"""
	Source checks listed in order of priority. Rearrange statements to change priority.
	For example, if OGLE is at the top of the if/elif chain, 
	and the event has both OGLE and MOA values available,
	then the OGLE values will be used to evaluate whether to trigger
	"""
	if updated_event.has_key("name_OGLE"):
		source = "OGLE"
	elif updated_event.has_key("name_ARTEMIS_OGLE"):
		source = "ARTEMIS_OGLE"
	elif updated_event.has_key("name_ARTEMIS_MOA"):
		source = "ARTEMIS_MOA"
	elif updated_event.has_key("name_MOA"):
		source = "MOA"

	evaluate_event_data(updated_event, source=source)
	# evaluate Einstein time, microlensing vs. cv status, and magnitude
	# for whether to trigger observation
	#evaluate_event_page_MOA(values_MOA)

def evaluate_event_data(event, source="OGLE"):
	"""Evaluate event using information from the survey event page or ARTEMIS file."""

	tE_key = "tE_" + source
	tE_err_key = "tE_err_" + source

	tE = event[tE_key]
	tE_err = event[tE_err_key]

	if check_einstein_time(tE, tE_err):
		event_trigger(event)
	else:
		logger.info("Einstein time failed: lower bound must be equal to or greater than " + str(MAX_EINSTEIN_TIME) + " days")

	"""
	# Check if event passes Einstein Time test
	if check_einstein_time(values_MOA["tE"], values_MOA["tE_err"]):
		# Check if event passes K2 microlensing region test
		if check_microlens_region(values_MOA["RA"], values_MOA["Dec"]):
			evaluate_assessment_and_mag_MOA(event_page_soup, values_MOA)
		else:
			logger.info("Microlensing region failed: Not in K2 Campaign 9 microlensing region")
	# fail to trigger if Einstein Time lower bound (Einstein time - Einstein time error) exceeds max Einstein Time threshold
	else:
		logger.info("Einstein time failed: lower bound must be equal to or greater than " + str(MAX_EINSTEIN_TIME) + " days")
	"""

def evaluate_assessment_and_mag_MOA(event_page_soup, values_MOA):
	# Parse page soup for microlensing assessment of event
	assessment = get_microlensing_assessment(event_page_soup)
	values_MOA["assessment"] = assessment

	if is_microlensing(assessment):
		# parse page soup for magnitude and error of most recent observation of event
		mag_values = event_data_collection.get_mag(event_page_soup)
		values_MOA["mag"] = mag_values[0]
		values_MOA["mag_err"] = mag_values[1]

		# trigger if magnitude matches critera along with the preceding checks
		if check_mag(mag_values):
			trigger_event(event_page_soup, values_MOA)

		# fail to trigger if mag and/or mag error values are unacceptable
		else:
			logger.info("Magnitude failed: must be brighter than " + str(MIN_MAG) + " AND have error less than " + str(MAX_MAG_ERR))

	# fail to trigger if assessment is non-microlensing
	else:
		logger.info("Assessment failed: Not assessed as microlensing")

def trigger_event(event):
	"""Runs when an event fits our critera. Triggers mail alerts and builds summary if those flags are on."""

	logger.info("Event is potentially suitable for observation!")
	if MAIL_ALERTS_ON:
		logger.info("Mailing event alert...")
		try:
			send_mail_alert(event)
		except Exception as ex:
			logger.warning("Exception attempting to mail event alert")
			logger.warning(ex)

	if SUMMARY_BUILDER_ON:
		logger.info("Building and outputting event summary page...")
		try:
			event_data_collection.build_summary(data_dict)
		except Exception as ex:
			logger.warning("Exception building/outputting event summary")
			logger.warning(ex)

	if EVENT_TRIGGER_RECORD_ON:
		logger.info("Saving event dictionary to dictionary of event dictionaries, to be outputted later..")
		try:
			add_event_to_trigger_dict(data_dict)
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
	mag_err_too_large = mag_values[2]
	logger.info("Magnitude: " + str(mag))
	logger.info("Magnitude error: " + str(mag_err))

	# more negative mags are brighter, so we want values less than
	# our minimum brightness magnitude	
	if mag > MIN_MAG or mag_err_too_large:
		return False
	else:
		return True

def add_event_to_trigger_dict(event_data_dict):
	"""Add event data dictionary (dictionary containing separate dictionaries for data from each survey) \
	to dictionary of event triggers, first converting it to a single event dictionary containing items from all surveys."""

	event = convert_data_dict(event_data_dict)

	# Use OGLE name for key pointing to event as value if availble.
	if event.has_key("name_OGLE") and event["name_OGLE"] != "":
		logger.info("Event has OGLE name")
		name_key = "name_OGLE"

	# Otherwise, use the MOA name.
	elif event.has_key("name_MOA") and event["name_MOA"] != "":
		logger.info("Event has MOA name and no OGLE name")
		name_key = "name_MOA"

	# If there is a neither a MOA nor OGLE name, something has gone wrong, and we abort storing the event.
	else:
		logger.warning("Event has neither OGLE nor MOA name item. Event:\n" + str(event))
		logger.warning("Aborting added event to event trigger dictionary...")
		return

	event_name = event[name_key]
	event_trigger_dict[event_name] = event

def convert_data_dict(event_data_dict):
	"""Convert event data dictionary (dictionary containing separate dictionaries for data from each survey) \
	for an event to proper format, combining data from all surveys into one dictionary."""

	"""
	event_data_dict is a dictionary of up to four event dictionaries for the same event.
	They contain MOA, OGLE, ARTEMIS_MOA, and ARTEMIS_OGLE values respectively.
	We convert this to a single dictionary with items from all surveys, and keys with survey suffixes attached
	to distinguish, for examle, tE_MOA from the tE_OGLE.
	"""
	logger.debug("Original event dict: " + str(event_data_dict))

	converted_event_dict = {}

	for fieldname in FIELDNAMES:
		if fieldname[-12:] == "_ARTEMIS_MOA" and event_data_dict.has_key("ARTEMIS_MOA") and event_data_dict["ARTEMIS_MOA"] != "":
			converted_event_dict[fieldname] = event_data_dict["ARTEMIS_MOA"][fieldname[:-12]]

		elif fieldname[-4:] == "_MOA" and fieldname[-12:] != "_ARTEMIS_MOA" and event_data_dict.has_key("MOA") and event_data_dict["MOA"] != "":
			converted_event_dict[fieldname] = event_data_dict["MOA"][fieldname[:-4]]

		elif fieldname[-13:] == "_ARTEMIS_OGLE" and event_data_dict.has_key("ARTEMIS_OGLE") and event_data_dict["ARTEMIS_OGLE"] != "":
			converted_event_dict[fieldname] = event_data_dict["ARTEMIS_OGLE"][fieldname[:-13]]

		elif fieldname[-5:] == "_OGLE" and fieldname[-13:] != "_ARTEMIS_OGLE" and event_data_dict.has_key("OGLE") and event_data_dict["OGLE"] != "":
			converted_event_dict[fieldname] = event_data_dict["OGLE"][fieldname[:-5]]

		# Convert the shortened names such as "2016-BLG-123" to the full names with survey prefixes,
		# like "MOA-2016-BLG-123" or "OGLE-2016"BLG-123";
		# Last condition Probably not necessary, but just in case
		if fieldname[:5] == "name_" and converted_event_dict.has_key(fieldname) and converted_event_dict[fieldname] != "":
			surveyName = fieldname[5:]
			converted_event_dict[fieldname] = surveyName + "-" + converted_event_dict[fieldname]

		logger.debug("Converted event dict: " + str(converted_event_dict))

	return converted_event_dict

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

def get_alert_level_and_message(values_MOA):
	"""Return alert level as "Warning" or "Alert" and related message depending on whether tE error exceeds our threshold constant""" 

	message = "Because the Einstein Time error is"
	tE_err = float(values_MOA["tE_err"])

	if tE_err <= EINSTEIN_TIME_ERROR_ALERT_THRESHOLD:
		alert_level = "Alert"
		message += " smaller than an error threshold of " + str(EINSTEIN_TIME_ERROR_ALERT_THRESHOLD)
	else:
		alert_level = "Warning"
		message += " greater than an error threshold of " + str(EINSTEIN_TIME_ERROR_ALERT_THRESHOLD)

	message += " day(s), this email has been given the status of \"Event %s\"." % str(alert_level)
	alertDict = {"alert level": alert_level, "message": message}
	logger.info("Event alert level: Event " + str(alertDict["alert level"]))
	
	return alertDict

def send_mail_alert(values_MOA):
	"""Send mail alert upon detecting short duration microlensing event"""
	event_name = values_MOA["name"]

	alert_level_dict = get_alert_level_and_message(values_MOA)
	alert_level = alert_level_dict["alert level"]
	alert_level_message = alert_level_dict["message"]

	mail_subject = event_name + " - Potential Short Duration Microlensing Event " + str(alert_level)
	summary_page_URL = "http://robonet.lcogt.net/robonetonly/WWWLogs/eventSummaryPages/" + event_name + "_summary.html"
	message_text = \
"""\
Potential Short Duration Microlensing Event %s
%s
Event Name: %s
Event ID: %s
Einstein Time (MOA): %s +/- %s
MOA Event Page: %s
Event summary page: %s\
""" % (alert_level, alert_level_message, event_name, values_MOA["ID"], values_MOA["tE"], values_MOA["tE_err"], values_MOA["pageURL"], summary_page_URL)
	mailAlert.send_alert(message_text, mail_subject, MAILING_LIST)
	logger.info("Event alert mailed!")

def main():
	run_ROGUE()

if __name__ == "__main__":
	main()
