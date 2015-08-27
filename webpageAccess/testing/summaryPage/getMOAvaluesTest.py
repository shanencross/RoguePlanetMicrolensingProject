from bs4 import BeautifulSoup
import requests
requests.packages.urllib3.disable_warnings()
from datetime import datetime
from astropy.time import Time

MAX_MAG_ERR = 0.7

def main():
	ID = "gb9-R-1-96634"
	nameURL = "https://it019909.massey.ac.nz/moa/alert2015/display.php?id=" + ID
	request = requests.get(nameURL, verify=False)
	page = request.content
	eventPageSoup = BeautifulSoup(page, 'lxml')

	microTable = eventPageSoup.find(id="micro").find_all('tr')

	tMax_line = microTable[0].find_all('td')
	tMaxJD = float(tMax_line[2].string.split()[1])

	tMax_splitString = tMax_line[4].string.split()
	tMaxJD_err = float(tMax_splitString[0])
	tMaxUT = str(tMax_splitString[2][1:-1])

	tE_line = microTable[1].find_all('td')
	tE = float(tE_line[2].string)
	tE_err = float(tE_line[4].string.split()[0])

	u0_line = microTable[2].find_all('td')
	u0 = float(u0_line[2].string)
	u0_err = float(u0_line[4].string)
	magList = getMag(eventPageSoup)
	if magList is not None:
		mag = magList[0]
		mag_err = magList[1]

	print "u0: %s +/- %s" % (u0, u0_err)
	print "tE: %s +/- %s" % (tE, tE_err)
	print "tMax (JD): %s +/- %s" % (tMaxJD, tMaxJD_err)
	print "tMax (UT): %s" % tMaxUT
	if magList is not None:
		print "mag: %s +/- %s" % (mag, mag_err)

	lCurvePlotURL = "https://it019909.massey.ac.nz/moa/alert2015/datab/plot-" + ID + ".png"
	print "Light curve plot:", lCurvePlotURL

def getMag(eventPageSoup):
	#Each magnitude is word 0 of string in table 3, row i, column 1 (zero-based numbering),
	#where i ranges from 2 through len(rows)-1 (inclusive).
	#Each error is word 1 of the same string.
	magTable = eventPageSoup.find(id="lastphot")
	rows = magTable.find_all('tr')

	#Iterate backwards over magnitudes starting from the most recent,
	#skipping over ones with too large errors
	for i in xrange(len(rows)-1, 1, -1):
		magStringSplit = rows[i].find_all('td')[1].string.split()
		mag = float(magStringSplit[0])
		magErr = float(magStringSplit[2])
		#print("Current magnitude: " + str(mag))
		#print("Current magnitude error: " + str(magErr))
		#Check if error exceeds max error allowed, and break out of loop if not.
		if (magErr <= MAX_MAG_ERR):
			magErrTooLarge = False
			#print("Magnitude error is NOT too large")
			break
		else:
			magErrTooLarge = True
			#print("Current magnitude error is too large")
	#If magnitude error is still too large after loop ends (without a break),
	#magErrTooLarge will be True.

	#if no magnitude rows were found in table, magnitude list is null
	if len(rows) > 2:
		magValues = (mag, magErr, magErrTooLarge)
	else:
		magValues = None

	return magValues

"""
#get dates, magnitudes, and errors from magnitude table
magTable = tables[3]
magFound = False
rows = magTable.find_all('tr')
mags = []
magErrs = []
datesHJD = []
datesUT =[]
for i in xrange(len(rows)-1, 1, -1):
	row = rows[i].find_all('td')
	dateStringSplit = row[0].string.split()
	magStringSplit = row[1].string.split()
	#print dateStringSplit
	mag = float(magStringSplit[0])
	magErr = float(magStringSplit[2])
	dateHJD = float(dateStringSplit[0])
	dateUT = str(dateStringSplit[1])
	mags.append(mag)
	magErrs.append(magErr)
	datesHJD.append(dateHJD)
	datesUT.append(dateUT)

print mags
print magErrs
print datesHJD
print datesUT
print
print magTable.find_all('tr')[0]
print
eventTable =tables[0].find_all('td')[1].string
print eventTable
"""

if __name__ == "__main__":
	main()
