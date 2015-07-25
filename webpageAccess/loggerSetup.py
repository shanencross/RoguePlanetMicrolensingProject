"""
loggerSetup.py
Purpose: Set up logger for webpageAccessTesting.py
Author: Shanen Cross
Date: 2015-07-22
"""
import os
import logging
from datetime import datetime

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

	#set up handlers
	fileHandler = logging.FileHandler(logFilepath) #for file output
	consoleHandler = logging.StreamHandler() #for console output
	fileHandler.setLevel(logging.DEBUG)
	consoleHandler.setLevel(logging.DEBUG)

	#set up log format
	fileFormatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")
	consoleFormatter = logging.Formatter(fmt="%(levelname)s - %(message)s")
	fileHandler.setFormatter(fileFormatter)
	consoleHandler.setFormatter(consoleFormatter)
	
	#add handlers to logger
	logger.addHandler(fileHandler)
	logger.addHandler(consoleHandler)

	return logger
