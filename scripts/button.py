#!../venv/bin/python

import paho.mqtt.client as mqtt
import yaml

with open('config.yaml') as config_f:
    config = yaml.safe_load(config_f)

mqttc = mqtt.Client(config['mqtt']['name'])
mqttc.connect(config['mqtt']['server'])
mqttc.publish("button/big/red/state", payload='pressed', qos=2, retain=True)