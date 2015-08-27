import sys
import os
DATA_DIR = "/science/robonet/rob/Operations/Signalmen_output/model"
MODEL_FILE = "KB150078.model"
MODEL_FILEPATH = os.path.join(DATA_DIR, MODEL_FILE)

EVENT_NAME = "2015-BLG-427"
IS_OGLE_NAME = False

#operations/autodownload events.txt
def getSignalmenValues(eventName):
	if IS_OGLE_NAME:
		filename = convertName_OGLE(eventName)
	else: #MOA name
		filename = convertName_MOA(eventName)
	modelFilepath = os.path.join(DATA_DIR, filename + ".model")

	with open(modelFilepath,'r') as file:
		line = file.readline()
	entries = line.split()
	t0_sig = float(entries[3]) + 2450000.0 #UTC?
	u0_sig = float(entries[7]) 
	tE_sig = float(entries[5]) #days?

	print "t0: %s" % t0_sig
	print "u0: %s" % u0_sig
	print "tE: %s" % tE_sig
	print "Event: %s" % eventName
	print "Filename: %s" % filename

def convertName_MOA(eventName):
	filename = "KB" + eventName[2:4] + "%04d" % int(eventName[9:])
	return filename

def convertName_OGLE(eventName):
	filename = "OB" + eventName[2:4] + "%04d" % int(eventName[9:])
	return filename

def main():
	if len(sys.argv) < 2:
		eventName = EVENT_NAME 
	else:
		eventName = sys.argv[1]
	getSignalmenValues(eventName)

if __name__ == "__main__":
	main()
	
