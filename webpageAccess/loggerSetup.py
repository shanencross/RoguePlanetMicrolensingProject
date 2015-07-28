"""
loggerSetup.py
Purpose: Set up logger for webpageAccessTesting.py
Author: Shanen Cross
Date: 2015-07-22
"""
import sys
import os
import logging
from datetime import datetime
CONSOLE_OUTPUT_ON = False

def setup(loggerName, logDir, logName, logDateTimeFormat):
	#create logger and construct filepath
	logger = logging.getLogger(loggerName)
	logDateTime = datetime.utcnow().strftime(logDateTimeFormat)
	logFilename = logName + "_" + logDateTime + ".log"
	logFilepath = os.path.join(logDir, logFilename)

	#create log directory if it does not already exist
	if not os.path.exists(logDir):
		os.makedirs(logDir)
	logger.setLevel(logging.DEBUG)

	#set up file handler
	fileHandler = logging.FileHandler(logFilepath) #for file output
	fileHandler.setLevel(logging.DEBUG)

	#set up log format
	fileFormatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")
	fileHandler.setFormatter(fileFormatter)
	
	#add file handler to logger
	logger.addHandler(fileHandler)

	#repeat above steps for console handler if console output is turned on
	if CONSOLE_OUTPUT_ON:
		consoleHandler = logging.StreamHandler() #for console output
		consoleHandler.setLevel(logging.DEBUG)
		consoleFormatter = logging.Formatter(fmt="%(levelname)s - %(message)s")
		consoleHandler.setFormatter(consoleFormatter)
		logger.addHandler(consoleHandler)

	return logger
