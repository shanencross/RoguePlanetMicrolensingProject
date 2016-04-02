#! /usr/bin/env python
'''
A more elaborate Python script to subscribe to MOA events. This will 
subscribe to both the main MOA channel as well as the test channel.
 - by Ian Bond 18/5/2015
 - modified by Shanen Cross 16/7/2015
'''
import getpass

# There are many XML modules out there, as well as some VOEvent parsing 
# modules. Here use the lxml module which allows one to issue XPath queries
from lxml import etree

from stompest.config   import StompConfig
from stompest.protocol import StompSpec
from stompest.sync     import Stomp

def xparam(voe, name):
    ''' Extract value for <Param element with given name attribute'''
    xstr = '//Param[@name="' + name + '"]/@value'
    return voe.xpath(xstr)[0]

def parse_voe(voe):
    '''Parse MOA VOEvent packet for selected information'''
    voe = etree.fromstring(voe)

    # Extract selected <Param name="xxx" value="xxx"/> elements from
    # the <What> stanza
    moa_id = xparam(voe, 'MOA_ID')
    field  = xparam(voe, 'field')
    colour = xparam(voe, 'colour')
    chip   = xparam(voe, 'chip')
    seqno  = xparam(voe, 'seq')
    int_id = '-'.join([field, colour, chip, seqno])

    # Coordinates and alert date from <WhereWhen>
    ra = voe.xpath('//C1/text()')[0]
    dec = voe.xpath('//C2/text()')[0]
    jd = voe.xpath('//TimeOffset/text()')[0]

    # Nature of the event from <Why>
    concept = '/'.join(voe.xpath('//Concept/text()'))
    
    return moa_id, int_id, ra, dec, jd, concept

def main(username, password):

    hostname = 'ec2-184-72-17-222.us-west-1.compute.amazonaws.com'
    port = '61613'

    # The names of the channels we will subscribe to
    channel1 = '/topic/moa.voevent'
    channel2 = '/topic/test.test'

    # Connect
    client = Stomp(StompConfig('tcp://' + hostname + ':' + port))
    client.connect(headers={'login': username, 'passcode': password})

    # Subscribe to each channel. For a durable subscription, a subscription 
    # name is associated with each channel
    for (name, channel) in [('topic1', channel1), ('topic2', channel2)]:
        client.subscribe(channel, headers={'activemq.subscriptionName' : name})

    while True:

        try:
            frame = client.receiveFrame()

            # We got a frame - from which channel did it come from?
            wherefrom = frame.headers['destination'] + ': '

            moa_id, int_id, ra, dec, jd, concept= parse_voe(frame.body)
            outs = wherefrom + ' '.join([moa_id, int_id, ra, dec, jd, concept])
            print outs

        except etree.XMLSyntaxError, e:
            outs = wherefrom + frame.body + ' (doesn\'t look like XML)'
            print str(e)
            print outs
        
        except KeyboardInterrupt:
            print "Disconnecting on keyboard interrupt ..."
            break

        except Exception, e:
            print "Something weird happened! "
            print str(e)
            print "Disconnecting ..."
            break
        #client.ack(frame)

    client.disconnect()
    print "Disconnected"

if __name__ == '__main__':

    # Prompt for username and password
    username = raw_input('Username > ')
    password = getpass.getpass('Password for ' + username + ' > ')
    main(username, password)
