import os
import httplib2
import oauth2client
from oauth2client import client
from oauth2client import tools
from apiclient import discovery

import listGmailMessages

user_id = "me"
query = "physics, is:unread"

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatability with Python 2.6
            credentials = tools.run(flow, store)
        print 'Storing credentials to ' + credential_path
    return credentials

def main():
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	service = discovery.build('gmail', 'v1', http=http)
	stop = False
	messages = listGmailMessages.ListMessagesMatchingQuery(service, user_id, query)

	for message in messages:
		if not stop:
			msg_id = message.get("id")
			print msg_id
			#print 'Message snippet: %s' % message['snippet']
			messageTrue = listGmailMessages.getMessage(service, user_id, msg_id)
			print messageTrue.keys()
			print
			stop = True
"""
	for message in messages:
		msg_id = message.get("id")
		print msg_id
		#print 'Message snippet: %s' % message['snippet']
		messageTrue = listGmailMessages.getMessage(service, user_id, msg_id)
		print messageTrue
		print
"""
if __name__ == "__main__":
	main()


