"""
event_data_collection.py
IN-USE ACTIVE COPY
Author: Shanen Cross
Date: 2016-03-21
Purpose: 
"""
import sys #for getting script directory
import os #for file-handling
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup #html parsing
import csv

import logger_setup
#import update_CSV

requests.packages.urllib3.disable_warnings()

DEBUGGING_MODE = True # Turn this flag on if modifying and testing code - turn it off when actively being used

#create and set up filepath and directory for logs -
#log dir is subdir of script
LOG_DIR = os.path.join(sys.path[0], "logs/event_data_collection_log")
LOG_NAME = "event_data_collection_log"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
if DEBUGGING_MODE:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=True, console_output_level = "DEBUG")
else:
	logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT, console_output_on=False, console_output_level = "DEBUG")


MAX_MAG_ERR = 0.7

#for accessing URLs; default value is current year, but buildPage() changes this to MOA event name year,
#in case it has been given an event from a year different year
CURRENT_YEAR = str(datetime.utcnow().year)
#CURRENT_YEAR = "2015" #JUST FOR TESTING/DEBUGGING - REMOVE
event_year_OGLE = CURRENT_YEAR
event_year_MOA = CURRENT_YEAR

#MOA and OGLE directories set to current year by defaultr; 
#buildPage() changes these if passed event from different year
MOA_dir = "https://it019909.massey.ac.nz/moa/alert" + event_year_MOA
if DEBUGGING_MODE:
	OGLE_dir = "http://ogle.astrouw.edu.pl/ogle4/ews/" #JUST FOR TESTING/DEBUGGING - REMOVE AND REPLACE WITH ABOVE COMMENTED LINE
else:
	OGLE_dir = "http://ogle.astrouw.edu.pl/ogle4/ews"

#comment this out when saving as in-use copy
if DEBUGGING_MODE:
	EVENT_FILENAME = "summary_page_test.html"
	EVENT_DIR = os.path.join(sys.path[0], "summary_page_output_tests_debugging")
	EVENT_FILEPATH = os.path.join(EVENT_DIR, EVENT_FILENAME)
	if not os.path.exists(EVENT_DIR):
		os.makedirs(EVENT_DIR)

ARTEMIS_DIR = "/science/robonet/rob/Operations/Signalmen_output/model"
if DEBUGGING_MODE:
	SUMMARY_OUTPUT_DIR = os.path.join(sys.path[0], "event_summary_pages_debugging")
	if not os.path.exists(SUMMARY_OUTPUT_DIR):
		os.makedirs(SUMMARY_OUTPUT_DIR)
else:
	#change SUMMARY_OUTPUT_DIR to the following when saving as in-use copy.
	#NOTE: Temporarily, output hardcoded to 2015 robonet log directory with TEMP_YEAR. Outputting to 2016 folder results 
	#in dead links #to summaries in email alerts. Only 2015 folder uploads to current URLs. Is the 2016 folder uploading to somewhere
	#else on the server?

	#NOTE 2: TEMP_YEAR isn't working anymore, so perhaps they updated things? No files from the 2015 folder are on the 
	#server anymore, only those in the 2016 folder. Now using CURRENT_YEAR instead.
	#TEMP_YEAR = "2015"
	SUMMARY_OUTPUT_DIR = "/science/robonet/rob/Operations/Logs/" + CURRENT_YEAR + "/WWWLogs/event_summary_pages"

"""
if DEBUGGING_MODE:
	EVENT_TRIGGER_RECORD_DIR = os.path.join(sys.path[0], "event_trigger_record_debugging")
else:
	# change EVENT_TRIGGER_RECORD_DIR to the following when saving as in-use copy:
	EVENT_TRIGGER_RECORD_DIR = os.path.join(sys.path[0], "event_trigger_record")

EVENT_TRIGGER_RECORD_FILENAME = "event_trigger_record.csv"
EVENT_TRIGGER_RECORD_FILEPATH = os.path.join(EVENT_TRIGGER_RECORD_DIR, EVENT_TRIGGER_RECORD_FILENAME)
if not os.path.exists(EVENT_TRIGGER_RECORD_DIR):
	os.makedirs(EVENT_TRIGGER_RECORD_DIR)
"""
if DEBUGGING_MODE:
	SURVEY_DATA_DIR = os.path.join(sys.path[0], "survey_data")
else:
	SURVEY_DATA_DIR = "/science/robonet/rob/Operations/SurveyData/"
MOA_DATA_FILEPATH = os.path.join(SURVEY_DATA_DIR, "MOA/moa_lenses.par")
OGLE_data_filepath = os.path.join(SURVEY_DATA_DIR, ("OGLE/lenses.par." + event_year_OGLE))

def collect_data(event):
	#values_MOA keywords: name, pageURL, tMax, tMax_err, tE, tE_err, u0, u0_err, mag, mag_err, assessment, lCurve, remarks, RA, Dec
	#values_OGLE keywords: name, pageURL, tMax, tMax_err, tE, tE_err, u0, u0_err, lCurve, lCurve_zoomed, remarks
	logger.info("--------------------------------------------")
	updated_event = {}
	event_year_OGLE = ""
	event_year_MOA = ""
	if event.has_key("name_OGLE"):
		logger.debug("The event has an OGLE name.")
		name_OGLE = event["name_OGLE"]
		event_year_OGLE = name_OGLE[5:9]

		logger.debug("Attempting to collect OGLE data...")
		updated_event.update(collect_data_OGLE(name_OGLE))
		logger.debug("Attempting to collect ARTEMIS data using OGLE name...")
		updated_event.update(collect_data_ARTEMIS(name_OGLE))

	if event.has_key("name_MOA"):
		logger.debug("The event has a MOA name.")
		name_MOA = event["name_MOA"]
		event_year_MOA = name_MOA[4:8]
		logger.debug("Attempting to collect MOA data...")
		updated_event.update(collect_data_MOA(name_MOA))
		logger.debug("Attempting to collect ARTEMIS data using MOA name...")
		updated_event.update(collect_data_ARTEMIS(name_MOA))

	update_year(event_year_OGLE, event_year_MOA)

	return updated_event

def build_summary(event):
	output_string = build_output_string(event)
	logger.info("Output:\n" + output_string)
	
	if not os.path.exists(SUMMARY_OUTPUT_DIR):
		os.makedirs(SUMMARY_OUTPUT_DIR)

	if event.has_key("name_OGLE"):
		event_name = event["name_OGLE"]
	elif event.has_key("name_MOA"):
		event_name = event["name_MOA"]
	else:
		logger.warning("Event has no OGLE or MOA name. Cannot build event summary.")
		logger.warning("Event dictionary: " + str(event))
		return

	output_filename = event_name + "_summary.html"
	output_filepath = os.path.join(SUMMARY_OUTPUT_DIR, output_filename)
	with open(output_filepath, 'w') as output_file:
		output_file.write(output_string)
	logger.info("--------------------------------------------")

#Update year and associated global URLs based on event years
def update_year(new_year_OGLE, new_year_MOA):
	if new_year_OGLE != "":
		global event_year_OGLE
		event_year_OGLE = new_year_OGLE
		global OGLE_data_filepath
		OGLE_data_filepath = os.path.join(SURVEY_DATA_DIR, ("OGLE/lenses.par." + event_year_OGLE))

		#OGLE dir remains unchanged unless event year differs rom the current year
		if event_year_OGLE != CURRENT_YEAR:
			global OGLE_dir
			OGLE_dir = "http://ogle.astrouw.edu.pl/ogle4/ews/" + event_year_OGLE

	if new_year_MOA != "":
		global event_year_MOA
		event_year_MOA = new_year_MOA
		global MOA_dir
		MOA_dir = "https://it019909.massey.ac.nz/moa/alert" + event_year_MOA

def collect_data_OGLE(event_name):
	name_URL = event_name[10:].lower()
	event_URL = OGLE_dir + "/" + name_URL + ".html"
	request = requests.get(event_URL, verify=False)
	page = request.content
	soup = BeautifulSoup(page, 'lxml')
	tables = soup.find_all("table")
	#logger.debug(str(soup))
	intro_table = tables[1]
	intro_table_rows = intro_table.find_all('tr')
	RA = str(intro_table_rows[2].find_all("td")[1].string).rstrip()
	Dec = str(intro_table_rows[3].find_all("td")[1].string).rstrip()
	remarks = str(intro_table_rows[4].find_all("td")[1].string)
	#remarks = str(soup.find(string="Remarks       ").next_element.string)
	
	if remarks == "\n":
		remarks = "None"

	param_table = tables[2]
	param_rows = param_table.find_all('tr')

	tMax_columns = param_rows[0].find_all('td')
	tau_columns = param_rows[1].find_all('td')
	u0_columns = param_rows[2].find_all('td')

	tMax_values = parse_values_OGLE(tMax_columns)
	tau_values = parse_values_OGLE(tau_columns)
	u0_values = parse_values_OGLE(u0_columns)

	lCurve_plot_URL = OGLE_dir + "/data/" + event_year_OGLE + "/" + name_URL + "/lcurve.gif"
	lCurve_plot_zoomed_URL = OGLE_dir + "/data/" + event_year_OGLE + "/" + name_URL + "/lcurve_s.gif"

	values = {"name_OGLE": event_name, "pageURL_OGLE": event_URL, "remarks_OGLE": remarks, \
								 "tMax_OGLE": tMax_values[0], "tMax_err_OGLE": tMax_values[1], \
								 "tE_OGLE": tau_values[0], "tE_err_OGLE": tau_values[1], \
								 "u0_OGLE": u0_values[0], "u0_err_OGLE": u0_values[1], \
								 "lCurve_OGLE": lCurve_plot_URL, "lCurve_zoomed_OGLE": lCurve_plot_zoomed_URL, \
								 "RA_OGLE": RA, "Dec_OGLE": Dec}

	logger.debug("OGLE values: " + str(values))
	return values

def parse_values_OGLE(columns):
	val = float(columns[1].string.split()[0])
	val_Err = float(columns[3].string.split()[0])
	return (val, val_Err)	

def collect_data_MOA(event_name):
	logger.debug("Getting RA and Dec in degrees and ID from MOA data file...")
	file_data_MOA = get_file_data_MOA(event_name)
	
	file_data_MOA_len = len(file_data_MOA)
	if file_data_MOA_len > 1:
		ID = file_data_MOA[1].rstrip()
	else:
		logger.warning("Cannot obtain MOA ID. Data list length is %s, which is < 2. Expected ID at position 1." % file_data_MOA_len)
		ID = ""

	if file_data_MOA_len > 2:
		RA_degrees = file_data_MOA[2].rstrip()
	else:
		logger.warning("Cannot obtain RA in degrees. Data list length is %s, which is < 3. Expected RA at position 2." % file_data_MOA_len)
		RA_degrees = ""

	if file_data_MOA_len > 3:
		Dec_degrees = file_data_MOA[3].rstrip()
	else:
		logger.warning("Cannot obtain Dec in degrees. Data list length is %s, which is < 4. Expected Dec at position 3." % file_data_MOA_len)
		Dec_degrees = ""

	logger.debug("Collecting MOA data from event survey page using MOA ID...")
	event_update = collect_data_MOA_via_ID(ID)

	if ID != "":
		event_update["ID_MOA"] = ID
	if RA_degrees != "":
		event_update["RA_degrees_MOA"] = RA_degrees
	if Dec_degrees != "":
		event_update["Dec_degrees_MOA"] = Dec_degrees

	logger.debug("MOA values: " + str(values_MOA))
	return event_update

def get_file_data_MOA(event_name):
	with open(MOA_DATA_FILEPATH, "r") as MOA_file:
		survey_data = []
		for line in MOA_file.read():
			line_split = line.split()
			line_event_name = line_split[0]
			
			if line_event_name == event_name:
				survey_data = line_split()	

		survey_data_len = len(survey_data)
		if survey_data_len < 1:
			logger.warning("MOA event %s not found in parameter file (located in %s)." % (event_name, MOA_DATA_FILEPATH))
			logger.warning("Returning empty list as survey file data.")
		elif survey_data_len < 4:
			logger.warning(("MOA event %s data file found (located in %s), " + \
						   "but there are too few items in the file's first line.") % (event_name, MOA_DATA_FILEPATH))
			logger.warning("There are %s items. Expected more than 3 items." % (survey_data_len))
			logger.warning("List obtained from splitting the first line of file:\n%s" % (str(survey_data)))

		return survey_data

def collect_data_MOA_via_ID(ID):
	name_URL = MOA_dir + "/display.php?id=" + ID
	request = requests.get(name_URL, verify=False)
	page = request.content
	soup = BeautifulSoup(page, 'lxml')
	micro_table = soup.find(id="micro").find_all('tr')

	tMax_line = micro_table[0].find_all('td')
	tMax_JD = float(tMax_line[2].string.split()[1])
	tMax_splitString = tMax_line[4].string.split()
	tMax_JD_err = float(tMax_splitString[0])
	tMaxUT = str(tMax_splitString[2][1:-1])
	tMax_JD_values = (tMax_JD, tMax_JD_err)

	tE_line = micro_table[1].find_all('td')
	tE = float(tE_line[2].string)
	tE_err = float(tE_line[4].string.split()[0])
	tE_values = (tE, tE_err)

	u0_line = micro_table[2].find_all('td')
	u0 = float(u0_line[2].string)
	u0_err = float(u0_line[4].string)
	u0_values = (u0, u0_err)

	mag_values = get_mag_MOA(soup)
	if mag_values is not None:
		mag = mag_values[0]
		mag_err = mag_values[1]
	
	RA = (soup.find(string="RA:").next_element.string).rstrip()
	Dec = (soup.find(string="Dec:").next_element.string).rstrip()
	assessment = soup.find(string="Current assessment:").next_element.string
	remarks = str(soup.find_all("table")[1].find("td").string)

	lCurve_plot_URL = MOA_dir + "/datab/plot-" + ID + ".png"
	values_MOA = {"name_MOA": event_name, "pageURL_MOA": name_URL, 
				  "tMax_MOA": tMax_JD_values[0], "tMax_err_MOA": tMax_JD_values[1], \
				  "tE_MOA": tE_values[0], "tE_err_MOA": tE_values[1], \
				  "u0_MOA": u0_values[0], "u0_err_MOA": u0_values[1], \
				  "mag_MOA": mag_values[0], "mag_err_MOA": mag_values[1], \
				  "lCurve_MOA": lCurve_plot_URL, "RA_MOA": RA, "Dec_MOA": Dec, \
				  "assessment_MOA": assessment, "remarks_MOA": remarks}
	return values_MOA	

def get_mag_MOA(event_page_soup):
	#Each magnitude is word 0 of string in table 3, row i, column 1 (zero-based numbering),
	#where i ranges from 2 through len(rows)-1 (inclusive).
	#Each error is word 1 of the same string.
	mag_table = event_page_soup.find(id="lastphot")
	rows = mag_table.find_all('tr')

	#Iterate backwards over magnitudes starting from the most recent,
	#skipping over ones with too large errors
	for i in xrange(len(rows)-1, 1, -1):
		mag_string_split = rows[i].find_all('td')[1].string.split()
		mag = float(mag_string_split[0])
		mag_err = float(mag_string_split[2])
		logger.debug("Current magnitude: " + str(mag))
		logger.debug("Current magnitude error: " + str(mag_err))
		#Check if error exceeds max error allowed, and break out of loop if not.
		if (mag_err <= MAX_MAG_ERR):
			mag_err_too_large = False
			#print("Magnitude error is NOT too large")
			break
		else:
			mag_err_too_large = True
			logger.debug("Current magnitude error is too large")
	#If magnitude error is still too large after loop ends (without a break),
	#mag_err_too_large will be True.

	#if no magnitude rows were found in table, magnitude list is null
	if len(rows) > 2:
		mag_values = (mag, mag_err, mag_err_too_large)
	else:
		mag_values = None
	return mag_values

def collect_data_ARTEMIS(event_name):

	survey_name = event_name.split("-")[0]	
	
	if survey_name == "MOA":
		logger.debug("Event has a MOA name. Using KB prefix.")
 		filename = "KB"
		event_name_short = event_name[4:]
	elif survey_name == "OGLE":
		logger.debug("Event has an OGLE name. Using OB prefix.")
		filename = "OB"
		event_name_short = event_name[5:]
	else:
		logger.warning("Event %s does not have OGLE or MOA survey prefix." % event_name)
		logger.warning("Cannot collect ARTEMIS data.")
		return {}
	filename += event_name_short[2:4] + "%04d" % int(event_name_short[9:])
	model_filepath = os.path.join(ARTEMIS_DIR, filename + ".model")

	logger.debug("Attempting to open ARTEMIS file %s ..." % model_filepath)
	if not os.path.isfile(model_filepath):
		logger.debug("No ARTEMIS file found.")
		return {}
	with open(model_filepath,'r') as file:
		logger.debug("Opened ARTEMIS file.")
		line = file.readline()
	entries = line.split()
	RA = (entries[0]).rstrip()
	Dec = (entries[1]).rstrip()
	t0 = float(entries[3]) + 2450000.0 #UTC(?)
	t0_err = float(entries[4])
	tE = float(entries[5]) #days
	tE_err = float(entries[6])
	u0 = float(entries[7]) 
	u0_err = float(entries[8])
	values = {("name_ARTEMIS_" + survey_name): filename, ("tMax_ARTEMIS_" + survey_name): t0, \
			  ("tMax_err_ARTEMIS_" + survey_name): t0_err, ("u0_ARTEMIS_" + survey_name): u0, \
			  ("u0_err_ARTEMIS_" + survey_name): u0_err, ("tE_ARTEMIS_" + survey_name): tE, \
			  ("tE_err_ARTEMIS_" + survey_name): tE_err, ("RA_ARTEMIS_" + survey_name): RA, \
			  ("Dec_ARTEMIS_" + survey_name): Dec}

	if survey_name == "MOA":
		logger.info("ARTEMIS MOA values: " + str(values))
	elif survey_name == "OGLE":
		logger.info("ARTEMIS OGLE values: " + str(values))
	return values

#values_MOA keywords: name, assessment, remarks, tMax, tMax_err, tE, tE_err, u0, u0_err, mag, mag_err, lCurve, RA, Dec
#values_OGLE keywords: name, remarks, tMax, tMax_err, tE, tE_err, u0, u0_err, lCurve, lCurve_zoomed
#values_ARTEMIS_MOA: name, tMax, tE, u0
def build_output_string(event):
	output_string = ""

	if event.has_key("name_OGLE"):
		output_string += \
"""\
<br>
<br>
OGLE event: <br> 
Event: <a href=%s>%s</a> <br>
Remarks: %s <br>
tMax: %s +/- %s <br>
tE: %s +/- %s <br>
u0: %s +/- %s <br>
Light Curve: <br>
<img src="%s" height=512 width=600> <br>
Light Curve Zoomed: <br>
<img src="%s" height=512 width=600> \
""" % (event["pageURL_OGLE"], event["name_OGLE"], event["remarks_OGLE"], event["tMax_OGLE"], event["tMax_err_OGLE"], \
		event["tE_OGLE"], event["tE_err_OGLE"], event["u0_OGLE"], event["u0_err_OGLE"], \
		event["lCurve_OGLE"], event["lCurve_zoomed_OGLE"])

	if event.has_key("name_MOA"):
		output_string += \
"""MOA event: <br>
Event: <a href=%s>%s</a> <br>
Assessment: %s <br>
Remarks: %s <br>
tMax: %s +/- %s <br>
tE: %s +/- %s <br>
u0: %s +/- %s <br>
Most recent magnitude: %s +/- %s <br>
Light Curve: <br>
<img src=%s width=500> \
""" % (event["pageURL_MOA"], event["name_MOA"], event["assessment_MOA"], event["remarks_MOA"], event["tMax_MOA"], \
	   event["tMax_err_MOA"], event["tE_MOA"], event["tE_err_MOA"], event["u0_MOA"], event["u0_err_MOA"], \
	   event["mag_MOA"], event["mag_err_MOA"], event["lCurve_MOA"])

	if event.has_key("name_ARTEMIS_MOA"):
		output_string += \
"""\
<br>
<br>
ARTEMIS values using MOA event: <br>
Event: %s <br>
tMax: %s +/- %s <br>
tE: %s +/- %s <br>
u0: %s +/-%s\
""" % (event["name_ARTEMIS_MOA"], event["tMax_ARTEMIS_MOA"], event["tMax_err_ARTEMIS_MOA"], event["tE_ARTEMIS_MOA"], \
	   event["tE_err_ARTEMIS_MOA"], event["u0_ARTEMIS_MOA"], event["u0_err_ARTEMIS_MOA"])

	if event.has_key("name_ARTEMIS_OGLE"):
		output_string += \
"""\
<br>
<br>
ARTEMIS values using OGLE event: <br>
Event: %s <br>
tMax: %s +/- %s <br>
tE: %s +/- %s <br>
u0: %s +/-%s\
""" % (event["name_ARTEMIS_OGLE"], event["tMax_ARTEMIS_OGLE"], event["tMax_err_ARTEMIS_OGLE"], event["tE_ARTEMIS_OGLE"], \
	   event["tE_err_ARTEMIS_OGLE"], event["u0_ARTEMIS_OGLE"], event["u0_err_ARTEMIS_OGLE"])

	tests = ["tE_test", "microlensing_assessment_test", "microlensing_region_test", "microlensing_region_alternate_test", "mag_test"]
	output_string += \
"""\
<br>
<br>
Tests:\
"""

	for test in tests:
		if event.has_key(test):
			output_string += \
"""\
<br>
%s status: %s\
""" % (test, event[test])


#For testing observation trigger button functionality
#	output_string += \
#"""\
#<br>
#<br>
#<form action=http://robonet.lcogt.net/cgi-bin/private/cgiwrap/robouser/buttonTesting.py>
#<input type = "submit" value = "submit" />
#</form>\
#"""
	return output_string

def test1():
	pass

def main():
	test1()

if __name__ == "__main__":
	main()
