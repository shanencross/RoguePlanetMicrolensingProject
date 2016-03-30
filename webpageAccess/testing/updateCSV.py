"""
updateCSV.py
Author: Shanen Cross
"""

import os
import csv

def update(fileOutputPath, newDict, fieldnames, delimiter=","):
# if csv file does NOT yet exist, open it for writing, sort the online TAP events by name, and store each event dictionary
	# as a row in this sequence
	if not os.path.isfile(fileOutputPath):
		#print "File does not exist. Opening file for writing..."
		with open(fileOutputPath, "w") as f:
			#print "File opened for writing."
			writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
			writer.writeheader()
			newNameList = sorted(newDict)
			#print "Sorted online TAP events: " + str(newNameList)
			for eventName in newNameList:
				eventDict = newDict[eventName]
				#print "Writing dict to file: " + str(eventDict)
				writer.writerow(eventDict)

	# if file does already exist, read the existing file, get the sorted combined list of names from both online and locally stored events,
	# then write to file, storing each event dictionary from this combined list as a row in sequence. 
	# Store the updated online event dictionary when its available, else keep the local dictionary.
	else: 
		#print "File already exists. Opening file for reading..."
		with open(fileOutputPath, "r") as f:
			#print "File opened for reading."
			reader = csv.DictReader(f, delimiter=delimiter)
			
			# get dictionary with names as keys and event dictionaries as values for locally stored events
			oldDict ={}
			for row in reader:
				if row.has_key("name_TAP"):
					nameKey = "name_TAP"

				elif row.has_key("name_OGLE"):
					nameKey = "name_OGLE"

				elif row.has_key("name_MOA"):
					nameKey = "name_MOA"

				else:
					print "Error: Event has no OGLE, MOA, or TAP name key."
					nameKey = ""

				eventName = row[nameKey]
				oldDict[eventName] = row		

			#print "Local TAP events: " + str(oldDict)
			#print "Online TAP events: " + str(newDict)
			# get set-like objects containing event names from local and online dictionaries,
			# then combine their set and sort it into an ordered list
			newNameSet = newDict.viewkeys()
			oldNameSet = oldDict.viewkeys()
			combinedNameList = sorted(newNameSet | oldNameSet)
			#print "combined set: " + str(newNameSet | oldNameSet)
			#print "combined TAP name list: " + str(combinedNameList)

		#print "Opening file for writing..."
		with open(fileOutputPath, "w") as f:
			#print "File opened for writing."
			#print "combined TAP name list: " + str(combinedNameList)
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
					print "Error: Somehow the name %s in the combined list %s is not in either the local (%s) or online (%s) name sets." % \
						  (name, combinedNameList, oldNameSet, newNameSet)
					eventDict = None
				#print "Writing event dictionary: " + str(eventDict)
				writer.writerow(eventDict)

def main():
	pass

if __name__ == "__main__":
	main()	
