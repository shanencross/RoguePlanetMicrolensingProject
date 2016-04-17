####################################
# IMPORT MODULES
from commands import getstatusoutput
from os import path

####################################
# FUNCTION: SEND ALERT
def send_alert(message,subject,mailinglist):
	'''Function to send an email alert'''

	alert = 'echo "'+message+'" | mail -s "'+subject+'" "'+','.join(mailinglist)+'"'
	(iexec, coutput) = getstatusoutput(alert)
	print str(iexec)
	return iexec
	print coutput

#####################################
# COMMANDLINE TEST SECTION:
if __name__ == '__main__':
	print "running cmdline test"
	message = 'LCOGT Quality Control Alert\n\nTest message\nNoresponse necessary'
	subject = 'LCOGT Quality Control Alert: System Test'
	mailinglist = [ 'shanencross@gmail.com' ]

	iexec = send_alert(message,subject,mailinglist)
