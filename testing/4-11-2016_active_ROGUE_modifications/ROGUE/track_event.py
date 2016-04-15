"""
track_event.py
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

event_page_soup = BeautifulSoup(requests.get(EVENT_PAGE_URL, verify=False).content, 'lxml')
tables = event_page_soup.find_all("table")
fit_parameter_table = tables[4]

dateTime = datetime.utcnow()
print "Current system UTC date/time: " + str(dateTime)

tMax_row = fit_parameter_table.find_all('tr')[0].find_all('td')
tMax = tMax_row[2].string.split()[1]
tMax_err = tMax_row[4].string.split()[0]
print "tMax: " + str(tMax) + \
	  " +/- " + str(tMax_err)

einstein_time_row = fit_parameter_table.find_all('tr')[1].find_all('td')
einstein_time = float(einstein_time_row[2].string)
einstein_time_err = float(einstein_time_row[4].string.split()[0])
print "Einstein time: " + str(einstein_time) + \
	  " +/- " +  str(einstein_time_err)

u0_row = fit_parameter_table.find_all('tr')[2].find_all('td')
u0 = float(u0_row[2].string)
u0_err = float(u0_row[4].string.split()[0])

print "u0: " + str(u0) + \
	   " +/- " + str(u0_err)

Ibase_row = fit_parameter_table.find_all('tr')[3].find_all('td')
Ibase = float(Ibase_row[2].string)
Ibase_err = float(Ibase_row[4].string.split()[0])

print "Ibase: " + str(Ibase) + \
      " +/- " + str(Ibase_err)

mag_table = tables[3]
newest_mag_row = mag_table.find_all('tr')[-1].find_all('td')
newest_mag_time = float(newest_mag_row[0].string.split()[0])
newest_mag = float(newest_mag_row[1].string.split()[0])
newest_mag_err = float(newest_mag_row[1].string.split()[2])
print "Newest mag time: " + str(newest_mag_time)
print "Newest mag: " + str(newest_mag) + \
	  " +/- " + str(newest_mag_err)
