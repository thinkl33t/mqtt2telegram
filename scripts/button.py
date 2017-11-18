#!../venv/bin/python

import os
import paho.mqtt.client as mqtt
import yaml

from telegram.ext import Updater, CommandHandler
from telegram import ParseMode, ChatAction

with open('config.yaml') as config_f:
    config = yaml.safe_load(config_f)

u = Updater(config['telegram']['token'])
u.start_polling()

mqttc = mqtt.Client(config['mqtt']['name'])
mqttc.connect(config['mqtt']['server'])
mqttc.publish("button/big/red/state", payload='pressed', qos=2, retain=True)
send_to_bot(":tada: Big Red Button pressed... :poop:")

def send_to_bot(message, increment=False):
    global u, config
    m = u.bot.sendMessage(chat_id=config['telegram']['chat_id'], text=message, parse_mode=ParseMode.MARKDOWN, disable_notification=True)

