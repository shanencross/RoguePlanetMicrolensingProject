"""
updateCSV.py
Author: Shanen Cross
"""

import sys
import os
import csv
import logging

import loggerSetup

LOG_DIR = os.path.join(sys.path[0], "updateCSVlog")
LOG_NAME = "updateCSVlog"
LOG_DATE_TIME_FORMAT = "%Y-%m-%d"
logger = loggerSetup.setup(__name__, LOG_DIR, LOG_NAME, LOG_DATE_TIME_FORMAT)

def update(fileOutputPath, newDict, fieldnames, delimiter=","):
	# if csv file does NOT yet exist, open it for writing, sort the online events by name, and store each event dictionary
	# as a row in this sequence
	logger.info("-------------------------------------------------------------------------------------")
	if not os.path.isfile(fileOutputPath):
		logger.info("File does not exist. Opening file for writing...")
		with open(fileOutputPath, "w") as f:
			logger.info("File opened for writing.")
			writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
			writer.writeheader()
			newNameList = sorted(newDict)
			logger.info("Sorted online events: " + str(newNameList))
			for eventName in newNameList:
				eventDict = newDict[eventName]
				logger.info("Writing dict to file: " + str(eventDict))
				writer.writerow(eventDict)

	# if file does already exist, read the existing file, get the sorted combined list of names from both online and locally stored events,
	# then write to file, storing each event dictionary from this combined list as a row in sequence. 
	# Store the updated online event dictionary when its available, else keep the local dictionary.
	else: 
		logger.info("File already exists. Opening file for reading...")
		with open(fileOutputPath, "r") as f:
			logger.info("File opened for reading.")
			reader = csv.DictReader(f, delimiter=delimiter)
			
			# get dictionary with names as keys and event dictionaries as values for locally stored events
			oldDict ={}
			for row in reader:
				if row.has_key("name_TAP") and row["name_TAP"] != "":
					nameKey = "name_TAP"

				elif row.has_key("name_OGLE") and row["name_OGLE"] != "":
					nameKey = "name_OGLE"

				elif row.has_key("name_MOA") and row["name_MOA"] != "":
					nameKey = "name_MOA"

				else:
					logger.warning("Error: Event row, " + str(row) + ", has no OGLE, MOA, or TAP name key.")
					nameKey = ""

				logger.info("Event row, " + str(row) + ", has name key: " +  str(nameKey))
				eventName = row[nameKey]
				logger.info("Event name: " + str(eventName))
				oldDict[eventName] = row
				logger.info("Stored event row " + str(row) + " in old dictionary with event name " + str(eventName) + " as key.")
				logger.info("Old dictionary: " + str(oldDict))

			logger.info("Local events: " + str(oldDict))
			logger.info("Online events: " + str(newDict))
			# get set-like objects containing event names from local and online dictionaries,
			# then combine their set and sort it into an ordered list
			newNameSet = newDict.viewkeys()
			oldNameSet = oldDict.viewkeys()
			combinedNameList = sorted(newNameSet | oldNameSet)
			logger.info("Old name set: " + str(oldNameSet))
			logger.info("New name set: " + str(newNameSet))
			logger.info("Combined name set: " + str(newNameSet | oldNameSet))
			logger.info("Sorted Combined name list: " + str(combinedNameList))

		logger.info("Opening file for writing...")
		with open(fileOutputPath, "w") as f:
			logger.info("File opened for writing.")
			logger.info("Sorted combined name list: " + str(combinedNameList))
			writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
			writer.writeheader()

			# Get and write the event dictionary for each event from the combined list in sequence. 
			# If available, get the online event. Otherwise, get the locally stored event.
			for name in combinedNameList:
				if name in newNameSet:
					eventDict = newDict[name]
				elif name in oldNameSet:
					eventDict = oldDict[name]
				else:
					logger.warning("Error: Somehow the name %s in the combined list %s is not in either the local (%s) or online (%s) name sets." % \
						  (name, combinedNameList, oldNameSet, newNameSet))
					eventDict = None
				logger.info("Writing event dictionary: " + str(eventDict))
				writer.writerow(eventDict)
	logger.info("-------------------------------------------------------------------------------------")

def main():
	pass

if __name__ == "__main__":
	main()	
