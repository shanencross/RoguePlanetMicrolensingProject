"""
trackEvent.py
Author - Shanen Cross
Date - 2015-07-30
Purpose: Will track values of an event over time and plot them as a function of time
"""

#EVENT_PAGE_URL = "https://it019909.massey.ac.nz/moa/alert2015//display.php?id=gb5-R-10-83651"
EVENT_PAGE_URL = "https://it019909.massey.ac.nz/moa/alert2015/display.php?id=gb10-R-7-74552"

import sys
import os
from datetime import datetime
import requests
requests.packages.urllib3.disable_warnings() #to disable warnings when accessing insecure sites
from bs4 import BeautifulSoup


"""
Just testing for now, starting off by correctly grabbing all of the
values we need froma given event page with HTML parsing.
"""

eventPageSoup = BeautifulSoup(requests.get(EVENT_PAGE_URL, verify=False).content, 'lxml')
tables = eventPageSoup.find_all("table")
fitParameterTable = tables[4]

dateTime = datetime.utcnow()
print "Current system UTC date/time: " + str(dateTime)

tMaxRow = fitParameterTable.find_all('tr')[0].find_all('td')
tMax = tMaxRow[2].string.split()[1]
tMaxErr = tMaxRow[4].string.split()[0]
print "tMax: " + str(tMax) + \
	  " +/- " + str(tMaxErr)

einsteinTimeRow = fitParameterTable.find_all('tr')[1].find_all('td')
einsteinTime = float(einsteinTimeRow[2].string)
einsteinTimeErr = float(einsteinTimeRow[4].string.split()[0])
print "Einstein time: " + str(einsteinTime) + \
	  " +/- " +  str(einsteinTimeErr)

u0_row = fitParameterTable.find_all('tr')[2].find_all('td')
u0 = float(u0_row[2].string)
u0err = float(u0_row[4].string.split()[0])

print "u0: " + str(u0) + \
	   " +/- " + str(u0err)

IbaseRow = fitParameterTable.find_all('tr')[3].find_all('td')
Ibase = float(IbaseRow[2].string)
IbaseErr = float(IbaseRow[4].string.split()[0])

print "Ibase: " + str(Ibase) + \
      " +/- " + str(IbaseErr)

magTable = tables[3]
newestMagRow = magTable.find_all('tr')[-1].find_all('td')
newestMagTime = float(newestMagRow[0].string.split()[0])
newestMag = float(newestMagRow[1].string.split()[0])
newestMagErr = float(newestMagRow[1].string.split()[2])
print "Newest mag time: " + str(newestMagTime)
print "Newest mag: " + str(newestMag) + \
	  " +/- " + str(newestMagErr)
