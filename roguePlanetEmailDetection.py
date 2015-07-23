import os #for iterating over files in folders
import logging
from datetime import datetime #for formatted date in log filename

#set up logger
logger = logging.getLogger(__name__)

#set up log directory and naming convention
logDir = "./logs/"
logName = "roguePlanetEmailDetectionLog"
logDateTimeFormat = "%Y-%m-%d_%H:%M:%S"
logDateTime = datetime.now().strftime(logDateTimeFormat)
logFilename = logName + "_" + logDateTime + ".log"
logFilepath = os.path.join(logDir, logFilename)
if not os.path.exists(logDir):
	os.makedirs(logDir)

#set email directory
emailDir = "./emails/"

#set up indicators for values to log
#Einstein Time
MOAtimeIndicator = "tE:"
OGLEtimeIndicator = "  tau"

#Base Magnitude
MOAmagIndicator = "Ibase:"
OGLEmagIndicator = "  I0"

def loggerSetup():
	logger.setLevel(logging.DEBUG)

	#set up handlers
	fileHandler = logging.FileHandler(logFilepath)
	consoleHandler = logging.StreamHandler()
	fileHandler.setLevel(logging.DEBUG)
	consoleHandler.setLevel(logging.DEBUG)

	#set up log format
	fileFormatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
	consoleFormatter = logging.Formatter(fmt="%(message)s")
	fileHandler.setFormatter(fileFormatter)
	consoleHandler.setFormatter(consoleFormatter)
	
	#add handlers to logger
	logger.addHandler(fileHandler)
	logger.addHandler(consoleHandler)

def getValue(line):
	lineWords = line.split()
	if len(lineWords) >= 2:
		value = float(lineWords[1])
		return value
	else:
		#print "ERROR: Line is too short"
		logger.error("Line \"" + line + "\" is too short")

def getEinsteinTime(line):
	einsteinTime = getValue(line)
	#print "Time: " + str(einsteinTime)
	logger.debug("Time: %s", einsteinTime)
	
def getMagnitude(line):
	mag = getValue(line)
	#print "Mag: " + str(mag)
	logger.debug("Mag: %s", mag)

	
def main():
	loggerSetup()
	logger.info("Beginning log")
	#iterate through email files
	logger.info("Searching through files")
	for filename in os.listdir(emailDir):
		filepath = os.path.join(emailDir, filename)
		if os.path.isfile(filepath):
			file = open(filepath, 'r')
			logger.info("Searching through file at path %s", filepath)
			for line in file:
				if line.startswith(MOAtimeIndicator):
					#print "MOA Time Hit!",
					logger.debug("MOA Time Hit!")
					getEinsteinTime(line)
				elif line.startswith(OGLEtimeIndicator):
					logger.debug("OGLE Time Hit!")
					#print "OGLE Time Hit!",
					getEinsteinTime(line)
				elif line.startswith(MOAmagIndicator):
					#print "MOA Mag Hit!",
					logger.debug("MOA Mag Hit!")
					getMagnitude(line)
				elif line.startswith(OGLEmagIndicator):
					#print "OGLE Mag Hit!",
					logger.debug("OGLE Mag Hit!")
					getMagnitude(line)
			file.close()

if __name__ == "__main__":
	main()


