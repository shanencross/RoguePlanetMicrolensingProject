"""
run_ROGUE_2_and_record_TAP.py
@author: Shanen Cross
Purpose: Execute TAP_table_recording.py folllowed by ROGUE.py to record TAP table and then run microlensing survey page check 
"""

import sys
import os
import logging

import ROGUE
import TAP_table_recording
import logger_setup
import mail_notification

DEBUGGING_MODE = True

if DEBUGGING_MODE:
	error_mailing_list = ["shanencross@gmail.com"]
else:
	#error_mailing_list = ["shanencross@gmail.com"]
	error_mailing_list = ["shanencross@gmail.com", "rstreet@lcogt.net"]

# if already running, return
if os.popen("ps -Af").read().count(__file__) > 1:
	mail_notification.send_notification("ROGUE 2.0 code exited because it was already running", "ROGUE 2.0 code exited", error_mailing_list)
	sys.exit(0)

# create and set up filepath and directory for logs -
# log dir is subdir of script
if DEBUGGING_MODE:
	LOG_DIR = os.path.join(sys.path[0], "logs_debugging/run_ROGUE_2_and_TAP_recorder_log")
	if not os.path.exists(LOG_DIR):
		os.makedirs(LOG_DIR)
else:
	LOG_DIR = "/science/robonet/rob/Operations/Logs/2016"
LOG_NAME = "run_ROGUE_2_and_TAP_recorder_log"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
logger = logger_setup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT)

def run_ROGUE_and_TAP_recorder():
	logger.info("----------------------------------------------------------------")
	try:
		logger.info("Running TAP table recorder...")
		TAP_table_recording.update_and_save_table()
	except Exception as ex:
		logger.warning("Exception recording TAP table.")
		logger.warning(ex)
		
	try:
		logger.info("Running ROGUE short duration microlensing alert system...")
		ROGUE_result = ROGUE.run_ROGUE()
		logger.info("ROGUE returned: %s" % str(ROGUE_result))
	except Exception as ex:
		logger.warning("Exception running ROGUE.")
		logger.warning(ex)
	logger.info("----------------------------------------------------------------")

def main():
	run_ROGUE_and_TAP_recorder()

if __name__ == "__main__":
	main()
