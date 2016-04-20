"""
logger_setup.py
IN-PROGRESS WORKING COPY
Purpose: Set up logger for webpageAccess.py and buildEventSummary.py
@author: Shanen Cross
Date: 2016-04-14
"""
import sys
import os
import logging
from datetime import datetime

def setup(logger_name, log_dir, log_name, log_date_time_format, console_output_on=False, console_output_level ="DEBUG"):
	#create logger and construct filepath
	logger = logging.getLogger(logger_name)
	log_date_time = datetime.utcnow().strftime(log_date_time_format)
	log_filename = log_name + "_" + log_date_time + ".log"
	log_filepath = os.path.join(log_dir, log_filename)

	#create log directory if it does not already exist
	if not os.path.exists(log_dir):
		os.makedirs(log_dir)

	if console_output_level == "DEBUG":
		logger.setLevel(logging.DEBUG)
	elif console_output_level == "INFO":
		logger.setLevel(logging.DEBUG)
	elif console_output_level == "WARNING":
		logger.setLevel(logging.WARNING)
	else: # Default
		logger.setLevel(logging.DEBUG)

	#set up file handler
	file_handler = logging.FileHandler(log_filepath) #for file output
	if console_output_level == "DEBUG":
		file_handler.setLevel(logging.DEBUG)
	elif console_output_level == "INFO":
		file_handler.setLevel(logging.INFO)
	elif console_output_level == "WARNING":
		file_handler.setLevel(logging.WARNING)
	else: # Default
		file_handler.setLevel(logging.DEBUG)

	#set up log format
	file_formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")
	file_handler.setFormatter(file_formatter)
	
	#add file handler to logger
	logger.addHandler(file_handler)

	#repeat above steps for console handler if console output is turned on
	if console_output_on:
		console_handler = logging.StreamHandler() #for console output

		if console_output_level == "DEBUG":
			console_handler.setLevel(logging.DEBUG)
		elif console_output_level == "INFO":
			console_handler.setLevel(logging.INFO)
		elif console_output_level == "WARNING":
			console_handler.setLevel(logging.WARNING)
		else: # Default
			console_handler.setLevel(logging.DEBUG)

		console_formatter = logging.Formatter(fmt="%(levelname)s - %(message)s")
		console_handler.setFormatter(console_formatter)
		logger.addHandler(console_handler)

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
