from bs4 import BeautifulSoup
import requests
requests.packages.urllib3.disable_warnings()
from datetime import datetime
from astropy.time import Time

request = requests.get("https://it019909.massey.ac.nz/moa/alert2015/display.php?id=gb9-R-1-96634", verify=False)
page = request.content
soup = BeautifulSoup(page, 'lxml')

"""
with open("./test.txt", 'w') as testFile:
	print soup.prettify()
	testFile.write(soup.prettify().encode("UTF-8"))
"""

"""
#Finding most recent magnitude in table
print soup.find(string="(arcsecs)").find_all_next('tr')[4].contents[1].string.split()[0]
print soup.find(string="(arcsecs)").next_element.contents[1].string.split()[0]

#either of these would probably be best
print soup.find_all("table")[3].contents[6].contents[1].string.split()[0]
print soup.find_all("table")[3].find_all('tr')[6].find_all('td')[1].string.split()[0]
"""

#Finding last observation time
obsTimeSplit = soup.find_all("table")[3].find_all('tr')[6].find_all('td')[0].string.split()
obsTimeHJD = obsTimeSplit[0]
obsTimeUTC = obsTimeSplit[1][1:-1] #[1:-1] Removes the parentheses

print "Time of last photometric observation"
print "HJD:", obsTimeHJD
print "UTC:", obsTimeUTC
print

#Finding discovery time
print "Discovery time"
discTime = soup.find("table").find_all('tr')[1].find_all('td')[1].string
print discTime
print

#tMax in JD
print "tMax in JD:"
tMaxJD = soup.find_all("table")[4].find_all('tr')[0].find_all('td')[2].string.split()[1]
print tMaxJD
#tMax in UT
print "tMax in UT:"
tMaxUT = soup.find_all("table")[4].find_all('tr')[0].find_all('td')[4].string.split()[2][1:-1]
print tMaxUT
print

#Current system time in UTC
nowUTC = datetime.utcnow()
print nowUTC
print

MAX_MAG_ERR = 0.04
magTable = soup.find_all("table")[3]
magFound = False
rows = magTable.find_all('tr')
for i in xrange(len(rows)-1, 1, -1):
	magStringSplit = rows[i].find_all('td')[1].string.split()
	mag = float(magStringSplit[0])
	magErr = float(magStringSplit[2])
	print "Mag:", mag
	print "Mag error:", magErr

	if (magErr <= MAX_MAG_ERR):
		magErrTooLarge = False
		break
	else:
		magErrTooLarge = True

print "Final mag:", mag
print "Final mag error:", magErr
print "Mag error too large:", magErrTooLarge
print

print len(magTable.find_all('tr'))
print

#Iterate backwards through each row in the magnitude table, from most to least recent
for row in reversed(magTable.find_all('tr')):
	#this lists all rows which contains magnitudes
	magnitudeRow = row.find_all('td')
	#if there are too few elements in the row, gone through all of the magnitude rows
	#(or encountered unexpected formatting)
	if len(magnitudeRow) < 3:
		break
	#get magn and error from column 1 string, where mag is word 0 and error is word 2
	magStringSplit = magnitudeRow[1].string.split()
	mag = float(magStringSplit[0])
	magErr = float(magStringSplit[2])
	print "Current magnitude: " + str(mag)
	print "Current magnitude error: " + str(magErr)
	if (magErr <= MAX_MAG_ERR):
		magErrTooLarge = False
		print "Magnitude error is NOT too large"
		break
	else:
		magErrTooLarge = True
		print "Current magnitude error is too large"

print "Final mag:", mag
print "Final mag error:", magErr
print "Mag error too large:", magErrTooLarge

"""
Pseudocode:
#after passing other tests for triggering observation
t1 = system time now
tMax = tMax

dt = abs(t1 - tMax)

if dt >= (1/2)*tE:
	observe!
else:
	do NOT observe
#What about error bars?

Example:
MOA 2015-BLG-392
tMax = JD 2457225.65 = UT 2015-Jul-22.15 = JD 2015-Jul-22-03:36:00.0
tE = 1.85 days
(1/2)*tE = 0.925 days
t1 = current time = 2015-07-23 22:17:34.549382 
dt =  abs(t1 - tMax) = 1.78 days
dt > (1/2)*tE
do NOT observe!

sigma(tMax) = 0.07 UT and sigma(tE) = 1.92 days
dt < (1/2)*(tE + sigma(t)) = (1/2)*(3.77) = 1.885
so, should we still should not observe?


MOA 2015-BLG-189
tMax = JD 2457192.9 = 2015-Jun-19.45 = 2015 June 19 09:36:00.0 UT
tE = 1.80 days
(1/2)*tE = 0.6 days
t1 = current time = 2015-07-23 22:17:34.549382 
dt = obviously more than 0.6 days
dt > (1/2)*tE
do NOT observe!

sigma(tMax) = 0.00 UT, sigma(tE) = 0.00 days

"""
