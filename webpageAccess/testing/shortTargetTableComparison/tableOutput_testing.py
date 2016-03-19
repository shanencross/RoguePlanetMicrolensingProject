events = [{"name":"MOA-123", "local":"yes", "TAP":"no"}, {"name":"OGLE-123", "local":"yes", "TAP":"yes"}, {"name":"OGLE-224", "local":"no", "TAP":"yes"}]

def main():
	with open("tableOutput_test.html", "w") as myFile:
		printPageStart(myFile)

		#print events to HTML file
		for event in events:
			print >> myFile, """<TR>"""
			printEvent(event, myFile)
			print >> myFile, """</TR>"""

		printPageEnd(myFile)

def printEvent(event, myFile):
	print >> myFile, """<TD ><a href=%s>%s</a></TD>""" % (getURL(event["name"]), event["name"])
	for key in ["local", "TAP"]:
		print >> myFile, """<TD >%s</TD>""" % event[key]

def getURL(eventName):
	return ""

def printPageStart(myFile):
	print >> myFile, \
"""<html>
<title>TAP - potential Kepler events</title><head><STYLE type="text/css">strong.topnav {background: #EFF5FB; color: #0000FF; text-align: center; padding-bottom: 0.2em; font-family: arial, helvetica, times; font-size: 10pt}a.plain {text-decoration:none; color: #0000FF} a:visited {text-decoration:none; color: blue} a.plain:hover {text-decoration:none; background: #819FF7; color: white}BODY { font-family: arial, helvetica, times; background: #FFFFFF; margin-left:0.2em; margin-right: 1em}.textheading {text-align: right; width: 70%; color: #819FF7; font-family: arial, helvetica, times; margin-top: 1.5em}.tablehead {color: #AAAAA; text-align: center; font-family: arial, helvetica, times; font-weight: bold}tablecontent {margin-top: 0.3em; margin-left: 0.2em; margin-bottom: 0.2em; font-family: arial, helvetica, times}.generic {font-family: arial, helvetica, times}.table {font-family: arial, helvetica, times; text-align: center}a:link {text-decoration:none;} a:visited {text-decoration:none; color: blue} a:hover {text-decoration:none; color: #819FF7}</STYLE></head><body>
<H2> Target List Comparison </H2>
<TABLE cellpadding="4" style="border: 1px solid #000000; border-collapse: collapse;" border="1">
 <TR>
  <TH>Event</TH>
  <TH>Local Trigger</TH>
  <TH>TAP Trigger</TH>
 </TR>
 <TR>"""

def printPageEnd(myFile):
	print >> myFile, """</TABLE>"""

if __name__ == "__main__":
	main()
