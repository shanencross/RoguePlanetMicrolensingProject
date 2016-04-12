"""
readingMasterList_test.py
@author: Shanen Cross
"""
NUM_START_INDEX_OGLE = 14
YEAR_START_INDEX_OGLE = 5
YEAR_END_INDEX_OGLE = YEAR_START_INDEX_OGLE + 4

NUM_START_INDEX_MOA = 13
YEAR_START_INDEX_MOA = 4
YEAR_END_INDEX_MOA = YEAR_START_INDEX_MOA + 4

def test1():
	input_filepath = "/science/robonet/rob/Operations/ExoFOP/master_events_list"
	newest_event_evaluated_OGLE = "OGLE-2016-BLG-0633"
	newest_event_evaluated_MOA = "MOA-2016-BLG-158"

	newest_year_OGLE = int(newest_event_evaluated_OGLE[YEAR_START_INDEX_OGLE:YEAR_END_INDEX_OGLE])
	newest_year_MOA = int(newest_event_evaluated_MOA[YEAR_START_INDEX_MOA:YEAR_END_INDEX_MOA])

	newest_num_OGLE = int(newest_event_evaluated_OGLE[NUM_START_INDEX_OGLE:])
	newest_num_MOA = int(newest_event_evaluated_MOA[NUM_START_INDEX_MOA:])

	print "Newest OGLE number: %s" % (str(newest_num_OGLE))
	print "Newest OGLE year: %s" % (str(newest_year_OGLE))
	print "Newest MOA number: %s" % (str(newest_num_MOA))
	print "Newest MOA year: %s" % (str(newest_year_MOA))

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


#			print """
#Name OGLE: %s
#Year OGLE: %s
#Num OGLE: %s
#Name MOA: %s
#Year MOA: %s
#Num MOA: %s\
#""" % (name_OGLE, year_OGLE, num_OGLE, name_MOA, year_MOA, num_MOA)

			if name_MOA == "MOA-2016-BLG-159":
				"""
				print name_MOA
				print num_MOA
				print year_MOA
				print name_OGLE
				print num_OGLE
				print year_OGLE
				print str(num_MOA != None)
				print str(num_MOA > newest_num_MOA)
				print newest_num_MOA
				print str(year_MOA != None)
				print str(year_MOA > newest_year_MOA)
				"""

			if num_OGLE != None and num_OGLE > newest_num_OGLE and year_OGLE != None and year_OGLE >= newest_year_OGLE:
				print "%s > %s" % (num_OGLE, newest_num_OGLE)
				print "%s > %s" % (year_OGLE, newest_year_OGLE)

				print "Match found!"
				print "Event: %s" % name_OGLE

			elif num_MOA != None and num_MOA > newest_num_MOA and year_MOA != None and year_MOA >= newest_year_MOA:
				print "%s > %s" % (num_MOA, newest_num_MOA)
				print "%s > %s" % (year_MOA, newest_year_MOA)

				print "Match found!"
				print "Event: %s" % name_MOA

			
		print "Completed checking file."

def main():
	test1()

if __name__ == "__main__":
	main()
