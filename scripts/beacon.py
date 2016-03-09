#!/usr/bin/python

import mosquitto
import yaml

config_f = open('../config.yaml')
config = yaml.safe_load(config_f)
config_f.close()

mqttc = mosquitto.Mosquitto('beacon292197392')
mqttc.connect(config['mqtt']['server'])
mqttc.publish("lights/beacon", 3000)
mqttc.disconnect()

