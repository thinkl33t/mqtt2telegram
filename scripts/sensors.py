#!/usr/bin/python

import requests

r = requests.get('http://spaceapi.hacman.org.uk/sensors.php')
j = r.json()
for s in j['sensor']['temperature']:
	sensor = j['sensor']['temperature'][s]
	print "*%s:* %s%s (_%s_) " % (sensor['location'], sensor['value'], sensor['unit'], sensor['last_update'])
