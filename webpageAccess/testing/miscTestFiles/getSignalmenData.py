import sys
import os
DATA_DIR = "/science/robonet/rob/Operations/Signalmen_output/model"
MODEL_FILE = "KB150078.model"
MODEL_FILEPATH = os.path.join(DATA_DIR, MODEL_FILE)

if len(sys.argv) < 2:
	eventName = "2015-BLG-378"
else:
	eventName = sys.argv[1]

#operations/autodownload events.txt
def getSignalmenValues(eventName):
	filename = convertName(eventName)
	modelFilepath = os.path.join(DATA_DIR, filename + ".model")

	with open(modelFilepath,'r') as file:
		line = file.readline()
	entries = line.split()
	t0_sig = float(entries[3]) + 2450000.0 #UTC?
	u0_sig = float(entries[7]) 
	tE_sig = float(entries[5]) #days?

	print t0_sig
	print u0_sig
	print tE_sig
	print eventName
	print filename

def convertName(eventName):
	filename = "KB" + eventName[2:4] + "%04d" % int(eventName[9:])
	return filename

def main():
	if len(sys.argv) < 2:
		eventName = "2015-BLG-378"
	else:
		eventName = sys.argv[1]
	getSignalmenValues(eventName)

if __name__ == "__main__":
	main()
	
