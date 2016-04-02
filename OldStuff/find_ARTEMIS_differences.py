import requests
import sys
import os
import logging
requests.packages.urllib3.disable_warnings()
OUTPUT_FILEPATH =  os.path.join(sys.path[0], "output2.txt")
ARTEMIS_DIR = "/science/robonet/rob/Operations/Signalmen_output/model"

def main():	
	crossReferenceURL = "https://it019909.massey.ac.nz/moa/alert2015/moa2ogle.txt"
	crossReferenceRequest = requests.get(crossReferenceURL, verify=False)
	crossReference = crossReferenceRequest.content.splitlines()
	mismatches = 0
	total = 0
	output = open(OUTPUT_FILEPATH, 'w')
	print >> output, "2015 events:"
	for line in crossReference:
		if line[0] != "#":
			files = []
			for event in line.split():
				filename = None
				if event[:3] == "MOA":
					eventName = event[4:]
					filename = "KB" + eventName[2:4] + "%04d" % int(eventName[9:]) + ".model"
				elif event[:4] == "OGLE":
					eventName = event[5:]
					filename = "OB" + eventName[2:4] + "%04d" % int(eventName[9:]) + ".model"
				if filename is not None:
					files.append(filename)
					total += 1
			filepaths = [os.path.join(ARTEMIS_DIR, files[0]), os.path.join(ARTEMIS_DIR, files[1])]
			fileA_exists = os.path.isfile(filepaths[0])
			fileB_exists = os.path.isfile(filepaths[1])
			if fileA_exists:
				with open(filepaths[0], 'r') as fileA:
					if fileB_exists:
						with open(filepaths[1], 'r') as fileB:
							fileA_contents = fileA.read()
							fileB_contents = fileB.read()

							fileA_contents_split = fileA_contents.split()
							fileB_contents_split = fileB_contents.split()
							if fileA_contents_split[:2] != fileB_contents_split[:2] or \
								fileA_contents_split[3:] != fileB_contents_split[3:]:
								mismatches += 1
								print >> output, "Mismatch:"
								print >> output, "%s:\n %s" % (files[0], fileA_contents) + "%s:\n %s" % (files[1], fileB_contents)
					else: #A exists, B does not exist
						print >> output, "%s exists, but its counterpart %s does not exist" % (files[0], files[1])
			else: #A does not exist
				if fileB_exists:
					print >> output, "%s exists, but its counterpart %s does not exist" % (files[1], files[0])
				else: #neither exist
					print >> output, "Neither %s nor %s exist" % (files[0], files[1])
	print >> output, "Number of mismatches: %s" % mismatches
	print >> output, "Total number of event pairs: %s" % (total/2)

if __name__ == "__main__":
	main()
