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
event_year = CURRENT_YEAR

#MOA and OGLE directories set to current year by defaultr; 
#buildPage() changes these if passed event from different year
MOA_dir = "https://it019909.massey.ac.nz/moa/alert" + event_year
if DEBUGGING_MODE:
	OGLE_dir = "http://ogle.astrouw.edu.pl/ogle4/ews/2015" #JUST FOR TESTING/DEBUGGING - REMOVE AND REPLACE WITH ABOVE COMMENTED LINE
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

#values_MOA keywords: name, pageURL, tMax, tMax_err, tE, tE_err, u0, u0_err, mag, mag_err, assessment, lCurve, remarks, RA, Dec
#values_OGLE keywords: name, pageURL, tMax, tMax_err, tE, tE_err, u0, u0_err, lCurve, lCurve_zoomed, remarks
def collect_data(event_page_soup, values_MOA, simulate=True):
	logger.info("--------------------------------------------")

	#set year to that of MOA event, for accessing URLs, and update MOA/OGLE URl directories
	update_year(values_MOA["name"].split("-")[0])

	#update the current MOA values with the remaining ones that still need to be pulled from the webpage 
	#(the errors, remarks, and lightcurve URL)
	remaining_values_MOA = get_remaining_values_MOA(event_page_soup, values_MOA["ID"])
	values_MOA.update(remaining_values_MOA)
	logger.debug("MOA values: " + str(values_MOA))
	name_OGLE = convert_event_name(values_MOA["name"], MOA_to_OGLE=True)
	if name_OGLE is not None:
		values_OGLE = get_values_OGLE(name_OGLE)
		values_ARTEMIS_OGLE = get_values_ARTEMIS(name_OGLE, is_MOA=False)
	else:
		values_OGLE = None
		values_ARTEMIS_OGLE = None
	values_ARTEMIS_MOA = get_values_ARTEMIS(values_MOA["name"], is_MOA=True)

	output_dict = {}
	if values_MOA is not None:
		output_dict["MOA"] = values_MOA
	if values_OGLE is not None:
		output_dict["OGLE"] = values_OGLE
	if values_ARTEMIS_MOA is not None:
		output_dict["ARTEMIS_MOA"] = values_ARTEMIS_MOA
	if values_ARTEMIS_OGLE is not None:
		output_dict["ARTEMIS_OGLE"] = values_ARTEMIS_OGLE

	return output_dict

def build_summary(values_dict):
	output_string = build_output_string(values_dict)
	logger.info("Output:\n" + output_string)
	
	if not os.path.exists(SUMMARY_OUTPUT_DIR):
		os.makedirs(SUMMARY_OUTPUT_DIR)
	output_filename = values_dict["MOA"]["name"] + "_summary.html"
	output_filepath = os.path.join(SUMMARY_OUTPUT_DIR, output_filename)
	with open(output_filepath, 'w') as output_file:
		output_file.write(output_string)
	logger.info("--------------------------------------------")

"""
def outputTable(input_dict):
	logger.info("Outputting table...")
	new_dict = {}
	
	#name_MOA, pageURL_MOA, tMax_MOA, tMax_err_MOA, tE_MOA, tE_err_MOA, u0_MOA, u0_err_MOA, mag_MOA, mag_err_MOA, assessment, lCurve_MOA, remarks_MOA
	#name_OGLE, pageURL_OGLE, tMax_OGLE, tMax_err_OGLE, tE_OGLE, tE_err_OGLE, u0_OGLE, u0_err_OGLE, mag_OGLE, mag_err_OGLE, lCurve_OGLE, lCurve_zoomed_OGLE, remarks_OGLE
	#name_ARTEMIS_MOA, tMax_ARTEMIS_MOA, tMax_err_ARTEMIS_MOA, tE_ARTEMIS_MOA, tE_err_ARTEMIS_MOA, u0_ARTEMIS_MOA, u0_err_ARTEMIS_MOA
	#name_ARTEMIS_OGLE, tMax_ARTEMIS_OGLE, tMax_err_ARTEMIS_OGLE, tE_ARTEMIS_OGLE, tE_err_ARTEMIS_OGLE, u0_ARTEMIS_OGLE, u0_err_ARTEMIS_OGLE


	fieldnames = ["name_MOA", "name_OGLE", "ID_MOA", "RA_MOA", "Dec_MOA", "tE_MOA", "tE_err_MOA", "tE_OGLE", "tE_err_OGLE", "tE_ARTEMIS_MOA", "tE_err_ARTEMIS_MOA", \
				  "tE_ARTEMIS_OGLE", "tE_err_ARTEMIS_OGLE", "u0_MOA", "u0_err_MOA", "u0_OGLE", "u0_err_OGLE", "u0_ARTEMIS_MOA", "u0_err_ARTEMIS_MOA", \
				  "u0_ARTEMIS_OGLE", "u0_err_ARTEMIS_OGLE", "mag_MOA", "mag_err_MOA"]
	delimiter = ","

	for fieldname in fieldnames:
		if fieldname[-12:] == "_ARTEMIS_MOA" and input_dict.has_key("ARTEMIS_MOA"):
			new_dict[fieldname] = input_dict["ARTEMIS_MOA"][fieldname[:-12]]

		elif fieldname[-4:] == "_MOA" and input_dict.has_key("MOA"):
			new_dict[fieldname] = input_dict["MOA"][fieldname[:-4]]

		elif fieldname[-13:] == "_ARTEMIS_OGLE" and input_dict.has_key("ARTEMIS_OGLE"):
			new_dict[fieldname] = input_dict["ARTEMIS_OGLE"][fieldname[:-13]]

		elif fieldname[-5:] == "_OGLE" and input_dict.has_key("OGLE"):
			new_dict[fieldname] = input_dict["OGLE"][fieldname[:-5]]

	logger.info("New dictionary: " + str(new_dict))

	update_CSV.update(EVENT_TRIGGER_RECORD_FILEPATH, new_dict, fieldnames=fieldnames, delimiter=delimiter)

	if os.path.isfile(EVENT_TRIGGER_RECORD_FILEPATH):
		with open(EVENT_TRIGGER_RECORD_FILEPATH, "a") as f:
			writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
			writer.writerow(new_dict)
	else:
		with open(EVENT_TRIGGER_RECORD_FILEPATH, "w") as f:
			writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
			writer.writeheader()
			writer.writerow(new_dict)
"""

#Update year and associated global URLs
def update_year(new_year):
	global event_year
	event_year = new_year

	global MOA_dir
	MOA_dir = "https://it019909.massey.ac.nz/moa/alert" + event_year

	#OGLE dir remains unchanged unless event year differs rom the current year
	if event_year != CURRENT_YEAR:
		global OGLE_dir
		OGLE_dir = "http://ogle.astrouw.edu.pl/ogle4/ews/" + event_year

#currently return dict of tMax err, tE err, u0 err, remarks, and lCurve URL, given soup and ID --
#Perhaps later, should be updated to return dict of all missing entries,
#given a partially full MOA values dict?
def get_remaining_values_MOA(event_page_soup, ID):
	micro_table = event_page_soup.find(id="micro").find_all('tr')
	tMax_JD_err = float(micro_table[0].find_all('td')[4].string.split()[0])
	tE_err = float(micro_table[1].find_all('td')[4].string.split()[0])
	u0_err = float(micro_table[2].find_all('td')[4].string)
	remarks = str(event_page_soup.find_all("table")[1].find("td").string)
	lCurve_plot_URL = MOA_dir + "/datab/plot-" + ID + ".png"
	update_values = {"tMax_err": tMax_JD_err, "tE_err": tE_err, "u0_err": u0_err, "lCurve": lCurve_plot_URL, "remarks": remarks}
	logger.debug("Updated values: " + str(update_values))
	return update_values

def convert_event_name(event_name, MOA_to_OGLE=True):
	cross_reference_URL = MOA_dir + "/moa2ogle.txt"
	cross_reference_request = requests.get(cross_reference_URL, verify=False)
	cross_reference = cross_reference_request.content.splitlines()
	if MOA_to_OGLE:
		initial_survey = "MOA"
		final_survey = "OGLE"
	else:
		initial_survey = "OGLE"
		final_survey = "MOA"

	event_name_initial = initial_survey + "-" + event_name
	event_name_final = ""
	for line in reversed(cross_reference):
		if line[0] != "#":
			line_split = line.split()
			if line_split[0] == event_name_initial:
				event_name_final = line_split[2]
				break
			if line_split[2] == event_name_initial:
				event_name_final = line_split[0]
				break
	if event_name_final == "":
		return None
	else:
		event_name_output = event_name_final[(len(final_survey) + 1):]
		logger.debug(initial_survey + " to " + final_survey + " converted name: " + str(event_name_final))
		return event_name_output

def get_values_OGLE(event_name):
	name_URL = event_name[5:].lower()
	event_URL = OGLE_dir + "/" + name_URL + ".html"
	request = requests.get(event_URL, verify=False)
	page = request.content
	soup = BeautifulSoup(page, 'lxml')
	tables = soup.find_all("table")
	logger.debug(str(soup))
	intro_table = tables[1]
	remarks = str(intro_table.find_all('tr')[4].find_all("td")[1].string)
	#remarks = str(soup.find(string="Remarks       ").next_element.string)

	if remarks == "\n":
		remarks = "None"

	param_table = tables[2]
	paramRows = param_table.find_all('tr')

	tMax_columns = paramRows[0].find_all('td')
	tau_columns = paramRows[1].find_all('td')
	u0_columns = paramRows[2].find_all('td')

	tMax_values = parse_values_OGLE(tMax_columns)
	tau_values = parse_values_OGLE(tau_columns)
	u0_values = parse_values_OGLE(u0_columns)

	lCurve_plot_URL = OGLE_dir + "/data/" + event_year + "/" + name_URL + "/lcurve.gif"
	lCurvePlotZoomedURL = OGLE_dir + "/data/" + event_year + "/" + name_URL + "/lcurve_s.gif"

	values = {"name": event_name, "pageURL": event_URL, "remarks": remarks, \
								 "tMax": tMax_values[0], "tMax_err": tMax_values[1], \
								 "tE": tau_values[0], "tE_err": tau_values[1], \
								 "u0": u0_values[0], "u0_err": u0_values[1], \
								 "lCurve": lCurve_plot_URL, "lCurve_zoomed": lCurvePlotZoomedURL}

	logger.debug("OGLE values: " + str(values))
	return values

def parse_values_OGLE(columns):
	val = float(columns[1].string.split()[0])
	val_Err = float(columns[3].string.split()[0])
	return (val, val_Err)

def get_values_MOA(ID):
	name_URL = MOA_dir + "/display.php?id=" + ID
	request = requests.get(name_URL, verify=False)
	page = request.content
	soup = BeautifulSoup(page, 'lxml')
	event_name = str(soup.find("title").string.split()[1])
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

	mag_values = getMag_MOA(soup)
	if mag_values is not None:
		mag = mag_values[0]
		mag_err = mag_values[1]
	
	assessment = soup.find(string="Current assessment:").next_element.string
	remarks = str(soup.find_all("table")[1].find("td").string)

	lCurve_plot_URL = MOA_dir + "/datab/plot-" + ID + ".png"
	values_MOA = {"name": event_name, "pageURL": name_URL, 
				  "tMax": tMax_JD_values[0], "tMax_err": tMax_JD_values[1], \
				  "tE": tE_values[0], "tE_err": tE_values[1], \
				  "u0": u0_values[0], "u0_err": u0_values[1], \
				  "mag": mag_values[0], "mag_err": mag_values[1], 
				  "lCurve": lCurve_plot_URL, "assessment": assessment, "remarks": remarks}

	logger.info("MOA values: " + str(values_MOA))
	return values_MOA	

def getMag_MOA(event_page_soup):
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
		#print("Current magnitude: " + str(mag))
		#print("Current magnitude error: " + str(mag_err))
		#Check if error exceeds max error allowed, and break out of loop if not.
		if (mag_err <= MAX_MAG_ERR):
			mag_err_too_large = False
			#print("Magnitude error is NOT too large")
			break
		else:
			mag_err_too_large = True
			#print("Current magnitude error is too large")
	#If magnitude error is still too large after loop ends (without a break),
	#mag_err_too_large will be True.

	#if no magnitude rows were found in table, magnitude list is null
	if len(rows) > 2:
		mag_values = (mag, mag_err, mag_err_too_large)
	else:
		mag_values = None

	logger.debug("Mag values: " + str(mag_values))
	return mag_values

def get_values_ARTEMIS(event_name, is_MOA=True):
	if is_MOA:
 		filename = "KB"
	else: #is OGLE
		filename = "OB"
	filename += event_name[2:4] + "%04d" % int(event_name[9:])
	model_filepath = os.path.join(ARTEMIS_DIR, filename + ".model")
	if not os.path.isfile(model_filepath):
		return None
	with open(model_filepath,'r') as file:
		line = file.readline()
	entries = line.split()
	t0 = float(entries[3]) + 2450000.0 #UTC(?)
	t0_err = float(entries[4])
	tE = float(entries[5]) #days
	tE_err = float(entries[6])
	u0 = float(entries[7]) 
	u0_err = float(entries[8])
	values = {"name": filename, "tMax": t0, "tMax_err": t0_err, "u0": u0, "u0_err": u0_err, "tE": tE, "tE_err": tE_err}
	if is_MOA:
		logger.info("ARTEMIS MOA values: " + str(values))
	else: # is OGLE
		logger.info("ARTEMIS OGLE values: " + str(values))
	return values

#values_MOA keywords: name, assessment, remarks, tMax, tMax_err, tE, tE_err, u0, u0_err, mag, mag_err, lCurve, RA, Dec
#values_OGLE keywords: name, remarks, tMax, tMax_err, tE, tE_err, u0, u0_err, lCurve, lCurve_zoomed
#values_ARTEMIS_MOA: name, tMax, tE, u0
def build_output_string(values_dict):
	if values_dict.has_key("MOA"):
		values_MOA = values_dict["MOA"]
	else:
		values_MOA = None

	if values_dict.has_key("OGLE"):
		values_OGLE = values_dict["OGLE"]
	else:
		values_OGLE = None

	if values_dict.has_key("ARTEMIS_MOA"):
		values_ARTEMIS_MOA = values_dict["ARTEMIS_MOA"]
	else:
		values_ARTEMIS_MOA = None

	if values_dict.has_key("ARTEMIS_OGLE"):
		values_ARTEMIS_OGLE = values_dict["ARTEMIS_OGLE"]
	else:
		values_ARTEMIS_OGLE = None

	output_string = ""

	if values_MOA is not None:
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
""" % (values_MOA["pageURL"], values_MOA["name"], values_MOA["assessment"], values_MOA["remarks"], values_MOA["tMax"], values_MOA["tMax_err"], \
		values_MOA["tE"], values_MOA["tE_err"], values_MOA["u0"], values_MOA["u0_err"], values_MOA["mag"], values_MOA["mag_err"], \
		values_MOA["lCurve"])

	if values_OGLE is not None:
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
""" % (values_OGLE["pageURL"], values_OGLE["name"], values_OGLE["remarks"], values_OGLE["tMax"], values_OGLE["tMax_err"], \
		values_OGLE["tE"], values_OGLE["tE_err"], values_OGLE["u0"], values_OGLE["u0_err"], \
		values_OGLE["lCurve"], values_OGLE["lCurve_zoomed"])

	if values_ARTEMIS_MOA is not None:
		output_string += \
"""\
<br>
<br>
ARTEMIS values using MOA event: <br>
Event: %s <br>
tMax: %s +/- %s <br>
tE: %s +/- %s <br>
u0: %s +/-%s\
""" % (values_ARTEMIS_MOA["name"], values_ARTEMIS_MOA["tMax"], values_ARTEMIS_MOA["tMax_err"], \
									values_ARTEMIS_MOA["tE"], values_ARTEMIS_MOA["tE_err"], \
									values_ARTEMIS_MOA["u0"], values_ARTEMIS_MOA["u0_err"])

	if values_ARTEMIS_OGLE is not None:
		output_string += \
"""\
<br>
<br>
ARTEMIS values using OGLE event: <br>
Event: %s <br>
tMax: %s +/- %s <br>
tE: %s +/- %s <br>
u0: %s +/-%s\
""" % (values_ARTEMIS_OGLE["name"], values_ARTEMIS_OGLE["tMax"], values_ARTEMIS_OGLE["tMax_err"], \
									values_ARTEMIS_OGLE["tE"], values_ARTEMIS_OGLE["tE_err"], \
									values_ARTEMIS_OGLE["u0"], values_ARTEMIS_OGLE["u0_err"])


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

def main():
	test2()

def test1():
	#MOA 2015-BLG-501
	#testID = "gb4-R-8-58133"
	#update_year("2015")
	#testID = "gb14-R-2-53554"	
	testID = "gb19-R-7-5172"
	values_MOA = get_values_MOA(testID)
	name_OGLE = convert_event_name(values_MOA["name"], MOA_to_OGLE=True)
	values_OGLE = get_values_OGLE(name_OGLE)
	values_ARTEMIS_MOA = get_values_ARTEMIS(values_MOA["name"], is_MOA=True)
	values_ARTEMIS_OGLE = get_values_ARTEMIS(name_OGLE, is_MOA=False)
	output_string = build_output_string(values_MOA, values_OGLE, values_ARTEMIS_MOA, values_ARTEMIS_OGLE)

	"""
	output_string += "MOA: <br>\n"
	for key in values_MOA.iterkeys():
		output_string += str(key) + ": " + str(values_MOA[key])
		output_string += "<br>\n"
	output_string += "<br>\n"
	output_string += "OGLE: <br>\n"
	for key in values_OGLE.iterkeys():
		output_string += str(key) + ": " + str(values_OGLE[key])
		output_string += "<br>\n"
	"""

	print output_string
	with open(EVENT_FILEPATH, 'w') as outputTest:
		outputTest.write(output_string)

def test2():
	testID = "gb19-R-7-5172"
	update_year("2016")

	values_MOA = get_values_MOA(testID)
	values_MOA.update({"RA":str(274.573436176), "Dec":str(-25.739123955)})
	name_OGLE = convert_event_name(values_MOA["name"], MOA_to_OGLE=True)
	values_OGLE = get_values_OGLE(name_OGLE)
	values_ARTEMIS_MOA = get_values_ARTEMIS(values_MOA["name"], is_MOA=True)
	values_ARTEMIS_OGLE = get_values_ARTEMIS(name_OGLE, is_MOA=False)

	output_dict = {}
	if values_MOA is not None:
		output_dict["MOA"] = values_MOA
	if values_OGLE is not None:
		output_dict["OGLE"] = values_OGLE
	if values_ARTEMIS_MOA is not None:
		output_dict["ARTEMIS_MOA"] = values_ARTEMIS_MOA
	if values_ARTEMIS_OGLE is not None:
		output_dict["ARTEMIS_OGLE"] = values_ARTEMIS_OGLE

	outputTable(output_dict)

if __name__ == "__main__":
	main()
