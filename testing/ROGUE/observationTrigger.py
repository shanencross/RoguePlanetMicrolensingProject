"""
observationTrigger.py
Author: Shanen Cross
"""

# import event_observer
from event_observer import event_observer
from dataCollectionAndOutput import eventDataCollection
from bs4 import BeautifulSoup # for testing only
import requests # for testing only

def triggerEventObservation(eventPageSoup, values, simulate=True):
	simulate = True
	if not simulate:
		# Change to simulate = False when saving active in-use copy; set to True again here for safety while testing
		simulate = True			
		#simulate = False

	observationParameters = getParameters(values, eventPageSoup, obs_sequence="short-te")
	
	# simulate hard-coded to True for safety while testing; change for active in-use copy
	observeEvent(observationParameters, simulate=True)

def getParameters(values, eventPageSoup, obs_sequence="short-te"):
	parameters = {}

	
	# values dict names have no survey prefix: "2016-BLG-001". This adds survey prefix : "MOA-2016-BLG-001";
	if values.has_key("survey"):
		surveyName = values["survey"]
	# If values dict does not have a key identifying the survey name, use MOA by default	
	else:
		surveyName = "MOA"

	eventName_long = surveyName + "-" + values["name"]
	parameters["name"] = eventName_long

	# Get sexigesimal RA and Dec
	sexigesimal_RA_and_Dec = eventDataCollection.get_sexigesimal_RA_and_Dec(eventPageSoup)
	parameters["ra"] = sexigesimal_RA_and_Dec["RA"]
	parameters["dec"] = sexigesimal_RA_and_Dec["Dec"]

	parameters["obs_sequence"] = obs_sequence

	return parameters
	

def observeEvent(observationParameters, simulate=True):

	# simulate = True hard-coded in now regardless of parameter passed in for safety;
	# change when saving active in-use copy
	submit_status = event_observer.observation_sequence( observationParameters, simulate=True )
	print str(submit_status)

def testObserveEvent():
	name = "MOA-2016-BLG-001"
	# name = "OGLE-2016-BLG-0001"
	ra = "17:51:48.02"
	dec = "-28:59:03.3"
	# obs_sequence = "short-te"

	observeEvent({"name": name, "ra": ra, "dec": dec}, simulate=True)

def testTriggerEventObservation():# access MOA event page and get soup of page for parsing more values
	eventPageURL = "https://it019909.massey.ac.nz/moa/alert2016/display.php?id=gb9-R-2-135883"
	values_MOA  = {"name": "2016-BLG-053"}
	
	eventPageSoup = BeautifulSoup(requests.get(eventPageURL, verify=False).content, 'lxml')

	triggerEventObservation(eventPageSoup, values_MOA, simulate=True)

def main():
	#testObserveEvent()
	testTriggerEventObservation()

if __name__ == "__main__":
	main()
