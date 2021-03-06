"""
readingMasterList_test.py
@author: Shanen Cross
"""

import sys
import os

CHECK_FILE = False

NUM_START_INDEX_OGLE = 14
YEAR_START_INDEX_OGLE = 5
YEAR_END_INDEX_OGLE = YEAR_START_INDEX_OGLE + 4

NUM_START_INDEX_MOA = 13
YEAR_START_INDEX_MOA = 4
YEAR_END_INDEX_MOA = YEAR_START_INDEX_MOA + 4

def test1():
	input_filepath = "/science/robonet/rob/Operations/ExoFOP/master_events_list"
	output_filepath = os.path.join(sys.path[0], "readingMasterList_outputTest.txt")
	
	if CHECK_FILE == True:
		newest_events_filepath = os.path.join(sys.path[0], "latest_events.txt")
		with open(newest_events_filepath, "r") as newest_event_file:
			newest_event_names = newest_event_file.read().split()
			newest_event_evaluated_OGLE = newest_event_names[0]
			newest_event_evaluated_MOA = newest_event_names[1]
	else:
		newest_event_evaluated_OGLE = "OGLE-2016-BLG-600"
		newest_event_evaluated_MOA = "MOA-2016-BLG-158"
	

	newest_year_OGLE = int(newest_event_evaluated_OGLE[YEAR_START_INDEX_OGLE:YEAR_END_INDEX_OGLE])
	newest_year_MOA = int(newest_event_evaluated_MOA[YEAR_START_INDEX_MOA:YEAR_END_INDEX_MOA])

	newest_num_OGLE = int(newest_event_evaluated_OGLE[NUM_START_INDEX_OGLE:])
	newest_num_MOA = int(newest_event_evaluated_MOA[NUM_START_INDEX_MOA:])


	with open(output_filepath, "w") as output_file:

		print >> output_file, "Newest OGLE number: %s" % (str(newest_num_OGLE))
		print >> output_file, "Newest OGLE year: %s" % (str(newest_year_OGLE))
		print >> output_file, "Newest MOA number: %s" % (str(newest_num_MOA))
		print >> output_file, "Newest MOA year: %s" % (str(newest_year_MOA))

		with open(input_filepath, "r") as masterList:
			for line in masterList:
				if line[0] == "#":
					continue

				lineSplit = line.split()
				name_OGLE = lineSplit[5]
				name_MOA = lineSplit[6]

				if name_OGLE == "None" or name_OGLE == "Unknown":
					year_OGLE = None
					num_OGLE = None
				else:
					year_OGLE = int(name_OGLE[YEAR_START_INDEX_OGLE:YEAR_END_INDEX_OGLE])
					num_OGLE = int(name_OGLE[NUM_START_INDEX_OGLE:])

				if name_MOA == "None" or name_MOA == "Unknown":		
					year_MOA = None
					num_MOA = None
				else:	
					year_MOA = int(name_MOA[YEAR_START_INDEX_MOA:YEAR_END_INDEX_MOA])
					num_MOA = int(name_MOA[NUM_START_INDEX_MOA:])

				if num_OGLE != None and num_OGLE > newest_num_OGLE and year_OGLE != None and year_OGLE >= newest_year_OGLE \
				and num_MOA != None and num_MOA > newest_num_MOA and year_MOA != None and year_MOA >= newest_year_MOA:

					print >> output_file, "%s > %s" % (num_OGLE, newest_num_OGLE)
					print >> output_file, "%s > %s" % (year_OGLE, newest_year_OGLE)

					print >> output_file, "%s > %s" % (num_MOA, newest_num_MOA)
					print >> output_file, "%s > %s" % (year_MOA, newest_year_MOA)

					print >> output_file, "Match found!"
					print >> output_file, "Event: %s" % name_OGLE
					print >> output_file, "Match found!"
					print >> output_file, "Event: %s" % name_MOA
					print >> output_file, "Both MOA and OGLE names found!"
					print >> output_file, "-------------------------------------"

			
				if num_OGLE == None and year_OGLE == None \
				 and num_MOA != None and num_MOA > newest_num_MOA and year_MOA != None and year_MOA >= newest_year_MOA:
					print >> output_file, "%s > %s" % (num_MOA, newest_num_MOA)
					print >> output_file, "%s > %s" % (year_MOA, newest_year_MOA)

					print >> output_file, "Match found!"
					print >> output_file, "Event: %s" % name_MOA
					print >> output_file, "No OGLE name"
					print >> output_file, "-------------------------------------"

				elif num_MOA == None and year_MOA == None \
				 and num_OGLE > newest_num_OGLE and year_OGLE != None and year_OGLE >= newest_year_OGLE:
			
					print >> output_file, "%s > %s" % (num_OGLE, newest_num_OGLE)
					print >> output_file, "%s > %s" % (year_OGLE, newest_year_OGLE)

					print >> output_file, "Match found!"
					print >> output_file, "Event: %s" % name_OGLE
					print >> output_file, "No MOA name"
					print >> output_file, "-------------------------------------"

				"""
				if num_OGLE != None and num_OGLE > newest_num_OGLE and year_OGLE != None and year_OGLE >= newest_year_OGLE:
					print >> output_file, "%s > %s" % (num_OGLE, newest_num_OGLE)
					print >> output_file, "%s > %s" % (year_OGLE, newest_year_OGLE)
	
					print >> output_file, "Match found!"
					print >> output_file, "Event: %s" % name_OGLE
	
				elif num_MOA != None and num_MOA > newest_num_MOA and year_MOA != None and year_MOA >= newest_year_MOA:
					print >> output_file, "%s > %s" % (num_MOA, newest_num_MOA)
					print >> output_file, "%s > %s" % (year_MOA, newest_year_MOA)
	
					print >> output_file, "Match found!"
					print >> output_file, "Event: %s" % name_MOA
					"""
			
			print >> output_file, "Completed checking file."
	
		output_file.close()

def main():
	test1()

if __name__ == "__main__":
	main()
