#!/usr/bin/python
from __future__ import print_function

import time
import yaml

from telegram import Updater,Bot,ParseMode
import mosquitto

config_f = open('config.yaml')
config = yaml.safe_load(config_f)
config_f.close()

bot = Bot(config['telegram']['token'])
u = Updater(bot=bot)
u.start_polling()

def send_to_bot(message):
    global bot, config
    bot.sendMessage(chat_id=config['telegram']['chat_id'], text=message, parse_mode=ParseMode.MARKDOWN, disable_notification=True)

def on_message(mosq, obj, msg):
    if msg.topic == 'door/outer/opened/username':
        send_to_bot("*%s* opened the outer door." % msg.payload)
    elif msg.topic == 'door/outer/buzzer':
        send_to_bot("%s" % random.choice(['Buzzer', 'Buzzer', 'Buzzer', 'Buzzer', 'Buzzer', 'Buzzer', 'Buzzer', 'Buzzer', 'Buzzer', 'rezzuB']))
    elif msg.topic == 'door/outer/invalidcard':
        send_to_bot("Unknown card at door")
    elif msg.topic == 'bot/outgoing':
        send_to_bot(msg.payload)
    elif msg.topic == 'door/shutter/state/open':
        send_to_bot("Shutter Opened!")
    elif msg.topic == 'door/shutter/state/closed':
        send_to_bot("Shutter Closed!")

mqttc = mosquitto.Mosquitto(config['mqtt']['name'])    
while True:
    mqttc.connect(config['mqtt']['server'])
    mqttc.subscribe("door/outer/#")
    mqttc.subscribe("bot/outgoing")
    mqttc.subscribe("door/shutter/state/#")
    mqttc.on_message = on_message
     
    while mqttc.loop(0.1) == 0:
        pass
    print ("MQTT connection lost!")
    mqttc.disconnect()
    time.sleep(5)

