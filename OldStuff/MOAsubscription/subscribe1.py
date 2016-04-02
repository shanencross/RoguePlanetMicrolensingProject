#! /usr/bin/env python
'''
Simplest python script to subscribe to MOA alerts.
  - by Ian Bond 18/5/2015
  - modified by Shanen Cross 16/7/2015
'''
import getpass

from stompest.config import StompConfig
from stompest.protocol import StompSpec
from stompest.sync import Stomp
from datetime import datetime

# You will be prompted to type in your username and password that you
# registered on the MOM
username = raw_input('Enter username > ')
password = getpass.getpass('Enter password for ' + username + ' > ')

# Set up a Stomp object with the URL to connect to the MOM
url = 'tcp://ec2-184-72-17-222.us-west-1.compute.amazonaws.com:61613'
client = Stomp(StompConfig(url))

# Connect - send a STOMP "CONNECT" frame
client.connect(headers={'login': username, 
                        'passcode': password, 
                        'client-id': username})

# Subscribe to the test channel - send a STOMP "SUBSCRIBE" frame
# Change channel name to '/topic/moa.voevent' to get real MOA events
subhdrs = {StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL}
client.subscribe('/topic/test', headers=subhdrs)

# Listen for new alerts in this loop

iteration = 0
while True:

    try: 
        print "Iteration: " + str(iteration)
        # Execution blocks here until a new frame is received
        frame = client.receiveFrame()

        # frame.body is a python string with the message that was published on 
        # the given channel. In this case this will be the XML VOEvent packet
        mypacket = frame.body

        # Now do whatever analysis you like on this packet. For example, use 
        # your favourite XML parser to extract the event parameters. Here, 
        # just dump the packet to the console
        print mypacket
        file = open(str(iteration) + "_subscribe1Test_" + str(datetime.now()))
        file.write(mypacket)
        file.close()
        iteration += 1

    except KeyboardInterrupt:
        print "Disconnecting ..."
        break

client.disconnect()
