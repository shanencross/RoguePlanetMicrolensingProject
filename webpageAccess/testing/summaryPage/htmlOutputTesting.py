#!/usr/bin/env python
#The above allows python script to be executed directly from the terminal after applying chmod +x
#or use: /opt/epd/bin/python (absolute pathname) for cgi scripts
htmlFile = open("./htmlOutputTest.htm", 'w')

tE_MOA = 2.5
tE_err_MOA = 0.2
u0_MOA = 1.2
u0_err_MOA = 0.3
tMax_MOA = 1000
tMax_err_MOA = 11


tE_OGLE = 2.8
tE_err_OGLE = 0.1
u0_OGLE = 1.8
u0_err_OGLE = 0.9
tMax_OGLE = 998
tMax_err_OGLE = 6

print >> htmlFile, ''' 
 <html> 
 <head> 
 <title> This is the title </title> 
 </head> 
 <body> 
 <br> 
 <FORM METHOD = get ACTION = "http://www.google.com">
 <INPUT TYPE = submit VALUE = "Google">
 <br>
 </form> 
 </body> 
 </html> 
 ''' 
