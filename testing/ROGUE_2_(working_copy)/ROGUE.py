"""
ROGUE.py
IN-USE ACTIVE COPY
Purpose: Poll MOA (and eventually OGLE) website for microlensing events, checking for ones likely to 
indicate rogue planets or planets distant from their parent star
Author: Shanen Cross
Date: 2016-04-21
"""
import sys # for getting script directory
import os # for file-handling
import logging
import csv
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
#LOG_DIR = os.path.join(sys.path[0], "logs/ROGUE_log")
LOG_DIR = "/science/robonet/rob/Operations/Logs/2016"
LOG_NAME = "ROGUE_log"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
if DEBUGGING_MODE:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=True, console_output_level = "DEBUG")
else:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=False, console_output_level = "DEBUG")

# set up filepath and directory for local copy of newest microlensing event
LOCAL_EVENTS_FILENAME = "last_events.txt"
if DEBUGGING_MODE:
	LOCAL_EVENTS_DIR = os.path.join(sys.path[0], "last_events_debugging")
else:
	LOCAL_EVENTS_DIR = os.path.join(sys.path[0], "last_events")
LOCAL_EVENTS_FILEPATH = os.path.join(LOCAL_EVENTS_DIR, LOCAL_EVENTS_FILENAME)
if not os.path.exists(LOCAL_EVENTS_DIR):
	os.makedirs(LOCAL_EVENTS_DIR)

# Set up filepath for .csv file of TAP event triggers
TAP_DIR = os.path.join(sys.path[0], "TAP_target_table")
TAP_FILENAME = "TAP_target_table.csv"
TAP_FILEPATH = os.path.join(TAP_DIR, TAP_FILENAME)

# Set up filepath for ROGUE vs. TAP comparison table HTML file
#COMPARISON_TABLE_DIR = os.path.join(sys.path[0], "comparison_table")
if DEBUGGING_MODE:
	COMPARISON_TABLE_DIR = os.path.join(sys.path[0], "comparison_table_debugging")
else:
	COMPARISON_TABLE_DIR = "/data/www/html/temp/shortte_alerts/new_version_test/comparison_table"

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
				  # NOTE: A global variable of the same name in event_data_collections
			      # needs to be changed in event_data_collection too if you want consistnecy
EINSTEIN_TIME_ERROR_NOTIFICATION_THRESHOLD = 1 # days - if Einstein Time error is less than this, email is labeled "Event Notification"; 
											   # otherwise email is labeled "Event Warning"
if DEBUGGING_MODE:
	EVENT_TRIGGER_RECORD_DIR = os.path.join(sys.path[0], "event_trigger_record_debugging")										
else:
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
#Possible criteria: tE, microlensing_assessment_MOA, K2_microlensing_superstamp_region, mag
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
	#MAILING_LIST = ["shanencross@gmail.com"]
	#MAILING_LIST = ["shanencross@gmail.com", "rstreet@lcogt.net", "calen.b.henderson@gmail.com"]
	MAILING_LIST = ["shanencross@gmail.com", "rstreet@lcogt.net", "calen.b.henderson@gmail.com", \
					"yossishv@gmail.com", "robonet-ops@lcogt.net", "david.p.bennett@nasa.gov", \
					"zhu.908@buckeyemail.osu.edu", "mpenny.astronomy@gmail.com", "radek.poleski@gmail.com", \
					"virginiebatista78@gmail.com"]

# Global dictionary of event triggers to update .csv file with
event_trigger_dict = {}
update_local_events = True

def run_ROGUE():
	logger.info("---------------------------------------")
	logger.info("Starting program")
	logger.info("Storing newest events in: " + LOCAL_EVENTS_FILEPATH)
	logger.info("Max Einstein Time allowed: " + str(MAX_EINSTEIN_TIME) + " days")
	logger.info("Dimmest magnitude allowed: " + str(MIN_MAG))
	logger.info("Max magnitude error allowed: " + str(MAX_MAG_ERR))

	newest_local_events = get_newest_local_events(filepath=LOCAL_EVENTS_FILEPATH)
	events_to_evaluate = reading_master_list.check_event_master_list(newest_local_events)
	logger.info("Events to evaluate:")
	for event in events_to_evaluate:
		if event.has_key("name_OGLE"):
			name_OGLE = event["name_OGLE"]
		else:
			name_OGLE = "N/A"

		if event.has_key("name_MOA"):
			name_MOA = event["name_MOA"]
		else:
			name_MOA = "N/A"

		logger.info("Event Name (OGLE): %s, Event Name (MOA): %s" % (name_OGLE, name_MOA))

	for event in events_to_evaluate:
		evaluate_event(event)
	
	logger.debug("Event trigger dictionary: %s" % str(event_trigger_dict))
	if event_trigger_dict and EVENT_TRIGGER_RECORD_ON:
		compare_triggers()
	#logger.debug(str(event_trigger_dict))

	# Save record of the newest OGLE event and newest MOA event
	# to be used to determine which events are new the next time
	# ROGUE runs

	if update_local_events:
		newest_events = get_newest_events(events_to_evaluate, newest_local_events)	
		save_newest_events(newest_events, filepath=LOCAL_EVENTS_FILEPATH)
	else:
		logger.warning("An exception occurred somewhere in the program's execution.")
		logger.warning("Not saving newest MOA event or newest OGLE event to file.")
		logger.warning("This set of new events should be evaluated again upon the program's next iteration.")
		# NOTE: SHOULD ADD CHECK ON MAIL ALERTS FOR WHETHER ALERT HAS BEEN SENT BEFORE OR NOT
	logger.info("Ending program")
	logger.info("---------------------------------------")
	return 0

def get_newest_local_events(filepath=LOCAL_EVENTS_FILEPATH):
	logger.info("Obtaining most recent MOA and OGLE events...")
	if not os.path.exists(filepath):
		logger.warning("File containing most recent MOA and OGLE events not found at %s." % (filepath)) 
		return None

	with open(filepath, "r") as events_file:
		events_split = events_file.read().split()
		event_name_OGLE = events_split[LOCAL_EVENT_OGLE_INDEX]
		event_name_MOA = events_split[LOCAL_EVENT_MOA_INDEX]
		
		events_dict = {"OGLE": event_name_OGLE, "MOA": event_name_MOA}
		logger.info("Most recently checked OGLE event: %s" % (events_dict["OGLE"]))
		logger.info("Most recently checked MOA event: %s" % (events_dict["MOA"]))
	return events_dict

def get_newest_events(new_events, newest_local_events):
	logger.info("Retrieving newest of newly checked events...")
	OGLE_names = [newest_local_events["OGLE"]]
	MOA_names = [newest_local_events["MOA"]]

	for event in new_events:
		
		if event.has_key("name_OGLE"):
			name_OGLE = event["name_OGLE"]
			OGLE_names.append(name_OGLE)

		if event.has_key("name_MOA"):
			name_MOA = event["name_MOA"]
			MOA_names.append(name_MOA)
		
	newest_OGLE = max(OGLE_names)
	newest_MOA = max(MOA_names)

	logger.info("Newest OGLE event: %s" % (newest_OGLE))
	logger.info("Newest MOA event: %s" % (newest_MOA))
	events_dict = {"OGLE": newest_OGLE, "MOA": newest_MOA}

	return events_dict

def save_newest_events(newest_events, filepath=LOCAL_EVENTS_FILEPATH):
	logger.info("Saving most recently checked events (%s and %s)..." % (newest_events["OGLE"], newest_events["MOA"]))
	logger.info("Filepath: %s" % filepath)
	with open(filepath, "w") as local_event_file:
		local_event_file.write("%s %s" % (newest_events["OGLE"], newest_events["MOA"]))
	logger.info("File saved.")

def evaluate_event(event):
	"""Evaluate whether event is short enough to potentially indicate a rogue planet
	and whether it is bright enough to be worth further observation.
	"""
	global update_local_events

	logger.info("")
	logger.info("Event Evaluation:")

	if event.has_key("name_OGLE"):
		name_OGLE = event["name_OGLE"]
	else:
		name_OGLE = "N/A"

	if event.has_key("name_MOA"):
		name_MOA = event["name_MOA"]
	else:
		name_MOA = "N/A"

	logger.info("Event Name (OGLE): %s, Event Name (MOA): %s" % (name_OGLE, name_MOA))

	# place relevant values from event row in MOA table into dictionary as strings for ease of access
	try:
		updated_event = event_data_collection.collect_data(event)
	except Exception as ex:
		logger.warning("Exception collecting data from survey site(s) and/or ARTEMIS")
		logger.warning(ex)
		update_local_events = False
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
	K2_microlensing_superstamp_region_test = "untested" # Checking exoFPO master event list for K2 superstamp
	K2_microlensing_superstamp_region_alternate_test = "untested" # Testing for K2 superstamp ourselves, with K2fov module
	mag_test = "untested"
	
	assessment_MOA = ""
	for source in sources:
		# Run Einstein time test (stricter, tE only check for now; pass in tE and tE_err if you want to include error check too)
		tE_key = "tE_" + source
		tE_err_key = "tE_err_" + source
		tE = event[tE_key]
		tE_err = event[tE_err_key]

		logger.info("For fit from source %s:" % (source))
		logger.info("Einstein time: %s +/- %s" % (tE, tE_err))
		#einstein_time_check = check_einstein_time(tE, tE_err)
		einstein_time_check = check_einstein_time(tE)
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
			mag_values = [event["mag_MOA"], event["mag_err_MOA"]]
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
					K2_microlensing_superstamp_region_alternate_test = "passed"
				else:
					K2_microlensing_superstamp_region_alternate_test = "failed"

	if event.has_key("passing_tE_sources"):
		event["passing_tE_sources"].sort()
		passing_tE_sources = event["passing_tE_sources"]
		passing_tE_sources_output = "Sources of passing tE values: "
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
			K2_microlensing_superstamp_region_test = "passed"
		else:
			K2_microlensing_superstamp_region_test = "failed"
	else:
		logger.warning("Event has no key in_K2_superstamp even though it should")
		logger.warning("Event:\n%s" % event)
	
	#DEBUG: Testing agreement with using K2 superstamp test ourselves, instead of relying on master list
	if DEBUGGING_MODE:
		K2_microlensing_superstamp_region_disagreement = False
		
		"""There is a disagreement between the two microlensiong region tests if
		they have different results and at least one of them has passed (ruling out the case where one
		is untested and the other has failed, which should not count as a disagreement)"""
		if K2_microlensing_superstamp_region_test != K2_microlensing_superstamp_region_alternate_test:
			if K2_microlensing_superstamp_region_test == "passed" or K2_microlensing_superstamp_region_alternate_test == "passed":
				microlensing_disagreement = True
		
		# If there is a disagreement, log information about it.
		if K2_microlensing_superstamp_region_disagreement:
			logger.warning("There is disagreement about the test for whether the event is in the K2 superstamp.")
			logger.warning("The test which uses the K2fov module, evaluating the RA and Dec from MOA, says that the event:")
			if K2_microlensing_superstamp_region_alternate_test == "passed":
				logger.warning("passes.")
			elif K2_microlensing_superstamp_region_alternate_test == "failed":
				logger.warning("does NOT pass.")
			elif K2_microlensing_superstamp_region_alternate_test == "untested":
				logger.warning("was not tested.")
			logger.warning("The exoFOP master event list test says that the event:")
			if K2_microlensing_superstamp_region_test == "passed":
				logger.warning("passes.")
			elif K2_microlensing_superstamp_region_test == "failed":
				logger.warning("does NOT pass.")	
				logger.warning("This means the superstamp entry in the master list is either False or Unknown.")
			elif K2_microlensing_superstamp_region_test == "untested":
				logger.warning("was not tested.")

	# Add test results to event dictionary
	event["tE_test"] = tE_test
	event["microlensing_assessment_test"] = microlensing_assessment_test
	event["K2_microlensing_superstamp_region_test"] = K2_microlensing_superstamp_region_test
	if DEBUGGING_MODE:
		event["K2_microlensing_superstamp_region_alternate_test"] = K2_microlensing_superstamp_region_alternate_test
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

	global update_local_events
	record_trigger = True

	logger.info("Event is potentially suitable for observation!")
	if MAIL_NOTIFICATIONS_ON:
		logger.info("Mailing event notification...")
		try:
			send_mail_notification(event)
		except Exception as ex:
			logger.warning("Exception attempting to build and send mail event notification")
			logger.warning(ex)
			update_local_events = False
			# Don't record the trigger if the mail was not sent
			record_trigger = False
			

	if SUMMARY_BUILDER_ON:
		logger.info("Building and outputting event summary page...")
		try:
			event_data_collection.build_summary(event)
		except Exception as ex:
			logger.warning("Exception building/outputting event summary")
			logger.warning(ex)
			update_local_events = False

	if EVENT_TRIGGER_RECORD_ON and record_trigger:
		logger.info("Saving event dictionary to dictionary of event dictionaries...")
		try:
			add_event_to_trigger_dict(event)
		except Exception as ex:
			logger.warning("Exception converting event data dictionary format and/or saving event to event trigger dictionary.")
			logger.warning(ex)
			update_local_events = False

		logger.info("Saving current event dictionary to file...")
		try:
			save_triggers()
		except Exception as ex:
			logger.warning("Exception attempting to save event triggers so far to event trigger record file.")
			logger.warning(ex)

def check_einstein_time(tE_string, tE_err_string=None):
	"""Check if Einstein time is short enough for observation."""
	einstein_time = float(tE_string)
	logger.debug("Evaluating Einstein Time: " + str(einstein_time) + " days")

	if tE_err_string != None and tE_err_string != "":
		einstein_time_err = float(tE_err_string)
		logger.debug("Evaluating Einstein Time Error: " + str(einstein_time_err) + " days")

		einstein_time_lower_bound = einstein_time - einstein_time_err
		logger.debug("Einstein Time Lower Bound = %s - %s = %s days" % (str(einstein_time), str(einstein_time_err), \
																	   str(einstein_time_lower_bound)))

	else:
		logger.debug("Not using error for Einstein time evaluation. Using Einstein time value as lower bound " + \
					 "for comparison with max Einstein time threshold.")
		einstein_time_lower_bound = einstein_time
		logger.debug("Einstein Time Lower Bound = %s days" % str(einstein_time_lower_bound))

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
	return inMicrolensRegion(RA, Dec)

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
	logger.debug("Added following event to event trigger dictionary: %s" % converted_event)

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

"""
def save_and_compare_triggers():
	if EVENT_TRIGGER_RECORD_ON:
		save_triggers()

		if EVENT_TABLE_COMPARISON_ON:
			compare_triggers()
"""

def save_triggers():
	global update_local_events

	logger.info("Outputting event to .csv record of event triggers...")
	try:
		update_CSV.update(EVENT_TRIGGER_RECORD_FILEPATH, event_trigger_dict, fieldnames=FIELDNAMES, delimiter=DELIMITER)
	except Exception as ex:
		logger.warning("Exception outputting .csv record of event triggers")
		logger.warning(ex)
		update_local_events = False
		return

def compare_triggers():
	global update_local_events

	logger.info("Generating and outputting HTML page with comparison table of ROGUE and TAP event triggers...")
	try:
		event_tables_comparison.compare_and_output(EVENT_TRIGGER_RECORD_FILEPATH, TAP_FILEPATH, COMPARISON_TABLE_FILEPATH)
	except Exception as ex:
		logger.warning("Exception generating/outputting comparison table HTML page")
		logger.warning(ex)
		update_local_events = Fals

def get_notification_level_and_message(event):
	"""Return notification level as "Warning" or "notification" and related message depending on whether tE error exceeds our threshold constant.""" 

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
	if notification_level == "Alert":
		message += " at least one of the Einstein times that passed our criteria has an error smaller than or equal to"
	elif notification_level == "Warning":
		message += " each of the Einstein times that passed our criteria has an error greater than"

	message += " an error threshold of " + str(EINSTEIN_TIME_ERROR_NOTIFICATION_THRESHOLD)
	message += " day(s), this email has been given the status of \"Event %s\"." % str(notification_level)
	notification_dict = {"notification level": notification_level, "message": message}
	logger.info("Event notification level: Event " + str(notification_dict["notification level"]))
	
	return notification_dict

def check_if_event_has_been_mailed_before(event):
	
	# If there is no trigger record yet, the event has not been mailed before
	if not os.path.exists(EVENT_TRIGGER_RECORD_FILEPATH):
		return False

	logger.info("Checking event trigger record for whether a mail notification has been triggered for this event previously...")
	with open(EVENT_TRIGGER_RECORD_FILEPATH, "r") as event_trigger_record_file:
			logger.info("Event trigger record opened for reading.")
			reader = csv.DictReader(event_trigger_record_file, delimiter=DELIMITER)
			for row in reader:
				if event.has_key("name_OGLE") and row.has_key("name_OGLE") and event["name_OGLE"] == row["name_OGLE"]:
					logger.warning("Event %s already found in event trigger record." % event["name_OGLE"])
					return True

				if event.has_key("name_MOA") and row.has_key("name_MOA") and event["name_MOA"] == row["name_MOA"]:
					logger.warning("Event %s already found in event trigger record." % event["name_MOA"])
					return True

			# If there is no match found, event alert has not been sent before
			logger.info("No record of this event having triggered a previous mail notification found.")
			return False

def send_mail_notification(event):
	if check_if_event_has_been_mailed_before(event):
		logger.warning("Event has already been mailed before.")
		logger.warning("Aborting mail notification.")
		logger.debug("Event that had been mailed before: %s" % str(event))
		return

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

""" % ( event["name_ARTEMIS_MOA"], event["tE_ARTEMIS_MOA"], event["tE_err_ARTEMIS_MOA"])

	mail_subject = "ROGUE: " + reference_event_name + " - Potential Short Duration Microlensing Event " + str(notification_level)
	summary_page_URL = "http://robonet.lcogt.net/temp/shortte_alerts/new_version_test/" + reference_event_name + "_summary.html"
	message_text += \
"""\
Event summary page: %s 

""" % (summary_page_URL)

	if DEBUGGING_MODE:
		tests = ["tE_test", "microlensing_assessment_test", "K2_microlensing_superstamp_region_test", "K2_microlensing_superstamp_region_alternate_test", "mag_test"]
	else:
		tests = ["tE_test", "microlensing_assessment_test", "K2_microlensing_superstamp_region_test", "mag_test"]

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

	logger.debug("Mail notification text:\n%s" % message_text)
	try:
		mail_notification.send_notification(message_text, mail_subject, MAILING_LIST)
	except Exception as ex:
		logger.warning("Exception attempting to send mail notification.")
		logger.warning(ex)
		raise		

	logger.info("Event notification mailed!")

def main():
	run_ROGUE()

if __name__ == "__main__":
	main()
