"""
buildEventSummaryPage.py
Author: Shanen Cross
Date: 2015-08-08
Purpose: Output summary of event information as an HTML page
"""

import sys #for getting script directory
import os #for file-handling
from bs4 import BeautifulSoup #html parsing
import getValuesTest


NAME_INDEX = 0
TMAX_INDEX = 1
TIME_INDEX = 2
U0_INDEX = 3
ASSESSMENT_INDEX = 4
MAG_INDEX = 5
REMARKS_INDEX = 6

#values_MOA: [event name, tMax, tE, u0, microlensing assessment, mag, remarks]
def buildPage(values_MOA, simulate=True):
	eventName_OGLE = getValuesTest.MOAtoOGLE(values_MOA[NAME_INDEX])


if __name__ == "__main__":
	main()

