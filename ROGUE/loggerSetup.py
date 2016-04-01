"""
loggerSetup.py
IN-PROGRESS WORKING COPY
Purpose: Set up logger for webpageAccess.py and buildEventSummary.py
Author: Shanen Cross
Date: 2017-03-08
"""
import sys
import os
import logging
from datetime import datetime
CONSOLE_OUTPUT_ON = False
CONSOLE_OUTPUT_LEVEL = "DEBUG" # INFO, DEBUG, WARNING... something else

def setup(loggerName, logDir, logName, logDateTimeFormat):
	#create logger and construct filepath
	logger = logging.getLogger(loggerName)
	logDateTime = datetime.utcnow().strftime(logDateTimeFormat)
	logFilename = logName + "_" + logDateTime + ".log"
	logFilepath = os.path.join(logDir, logFilename)

	#create log directory if it does not already exist
	if not os.path.exists(logDir):
		os.makedirs(logDir)

	if CONSOLE_OUTPUT_LEVEL == "DEBUG":
		logger.setLevel(logging.DEBUG)
	elif CONSOLE_OUTPUT_LEVEL == "INFO":
		logger.setLevel(logging.DEBUG)
	elif CONSOLE_OUTPUT_LEVEL == "WARNING":
		logger.setLevel(logging.WARNING)
	else: # Default
		logger.setLevel(logging.DEBUG)

	#set up file handler
	fileHandler = logging.FileHandler(logFilepath) #for file output
	if CONSOLE_OUTPUT_LEVEL == "DEBUG":
		fileHandler.setLevel(logging.DEBUG)
	elif CONSOLE_OUTPUT_LEVEL == "INFO":
		fileHandler.setLevel(logging.INFO)
	elif CONSOLE_OUTPUT_LEVEL == "WARNING":
		fileHandler.setLevel(logging.WARNING)
	else: # Default
		fileHandler.setLevel(logging.DEBUG)



	#set up log format
	fileFormatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")
	fileHandler.setFormatter(fileFormatter)
	
	#add file handler to logger
	logger.addHandler(fileHandler)

	#repeat above steps for console handler if console output is turned on
	if CONSOLE_OUTPUT_ON:
		consoleHandler = logging.StreamHandler() #for console output

		if CONSOLE_OUTPUT_LEVEL == "DEBUG":
			consoleHandler.setLevel(logging.DEBUG)
		elif CONSOLE_OUTPUT_LEVEL == "INFO":
			consoleHandler.setLevel(logging.INFO)
		elif CONSOLE_OUTPUT_LEVEL == "WARNING":
			consoleHandler.setLevel(logging.WARNING)
		else: # Default
			consoleHandler.setLevel(logging.DEBUG)

		consoleFormatter = logging.Formatter(fmt="%(levelname)s - %(message)s")
		consoleHandler.setFormatter(consoleFormatter)
		logger.addHandler(consoleHandler)

	"""This prevents logger from duplicating command line output. For example, if you call logger.info("Hello world") without this
	from webpageAccess.py after setting up the logger, the command line output will look like:

	INFO - Hello world
	INFO:__main__:Hello world

	...but the log on file will read:

	INFO - Hello world

	...as it should.

	This only occurs if I have imported anything from the K2fov module. If I remove the import, logger works as it should without duplication.
	My other imports don't affect the logger and I don't know why importing K2fov (or its submodules) affects the logger like this. 
	Setting propagate to False appears to stop the duplication, at least.
	"""
	logger.propagate = False

	return logger
