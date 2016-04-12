"""
readingMasterList_test.py
@author: Shanen Cross
"""

MOA_NUM_START_INDEX = 13
OGLE_NUM_START_INDEX = 14

def test1():
	input_filepath = "/science/robonet/rob/Operations/ExoFOP/master_events_list"
	newest_OGLE_event_evaluated = "OGLE-2016-BLG-0633"
	newest_MOA_event_evaluated = "MOA-2016-BLG-158"

	newest_OGLE_num = int(newest_OGLE_event_evaluated[OGLE_NUM_START_INDEX:])
	newest_MOA_num = int(newest_MOA_event_evaluated[MOA_NUM_START_INDEX:])

	print "Newest OGLE number: %s" % (str(newest_OGLE_num))
	print "Newest MOA number: %s" % (str(newest_MOA_num))

	with open(input_filepath, "r") as masterList:
		for line in masterList:
			lineSplit = line.split()
			name_OGLE = lineSplit[5]
			name_MOA = lineSplit[6]
			
			num_MOA = name_MOA[MOA_NUM_START_INDEX:]
			num_OGLE = name_OGLE[OGLE_NUM_START_INDEX:]

			
		print "Completed checking file."

def main():
	test1()

if __name__ == "__main__":
	main()
