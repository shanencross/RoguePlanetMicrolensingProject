from bs4 import BeautifulSoup
import requests
requests.packages.urllib3.disable_warnings()
from datetime import datetime
from astropy.time import Time

request = requests.get("https://it019909.massey.ac.nz/moa/alert2015/moa2ogle.html", verify=False)
page = request.content
soup = BeautifulSoup(page, 'lxml')

x = soup.find("table").find_all('tr').next_element
print x


