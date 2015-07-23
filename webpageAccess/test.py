from bs4 import BeautifulSoup
import requests
requests.packages.urllib3.disable_warnings()
from datetime import datetime

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
print soup.find("table").find_all('tr')[1].find_all('td')[1].string
print

#JD tMax
print "tMax in JD:"
print soup.find_all("table")[4].find_all('tr')[0].find_all('td')[2].string.split()[1]
#UT tMax
print "tMax in UT:"
print soup.find_all("table")[4].find_all('tr')[0].find_all('td')[4].string.split()[2][1:-1]
