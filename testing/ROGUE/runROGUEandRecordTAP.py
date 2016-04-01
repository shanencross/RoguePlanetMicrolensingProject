"""
runROGUEandRecordTAP.py
Author: Shanen Cross
Purpose: Execute TAPtableRecording.py folllowed by ROGUE.py to record TAP table and then run microlensing survey page check 
"""

import sys
import os
import logging

import ROGUE
import TAPtableRecording
import loggerSetup

# create and set up filepath and directory for logs -
# log dir is subdir of script
LOG_DIR = os.path.join(sys.path[0], "logs/runROGUEandTAPrecorderLog")
LOG_NAME = "runROGUEandTAPrecorderLog"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
logger = loggerSetup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT)

def runROGUEandTAPrecorder():
	logger.info("----------------------------------------------------------------")
	try:
		logger.info("Running TAP table recorder...")
		TAPtableRecording.updateAndSaveTable()
	except Exception as ex:
		logger.warning("Exception recording TAP table.")
		logger.warning(ex)
		
	try:
		logger.info("Running ROGUE short duration microlensing alert system...")
		ROGUE.runROGUE()
	except Exception as ex:
		logger.warning("Exception running ROGUE.")
		logger.warning(ex)
	logger.info("----------------------------------------------------------------")

def main():
	runROGUEandTAPrecorder()

if __name__ == "__main__":
	main()
