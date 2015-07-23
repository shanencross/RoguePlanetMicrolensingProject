import imaplib
mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('shanencross@gmail.com', 'IwoaSCigGtyo')

mail.list()
# Out: list of "folders" aka labels in gmail.
mail.select("inbox")  # connect to inbox.

result, messages = mail.search(None, "UNSEEN")

if result == 'OK':
	for message in messages: 
		print message
