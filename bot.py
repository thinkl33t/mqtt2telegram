#!/usr/bin/python
from __future__ import print_function

import time
import yaml
import os
import re
import subprocess
import logging

from telegram import Updater,Bot,ParseMode, ChatAction
import mosquitto

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

config_f = open('config.yaml')
config = yaml.safe_load(config_f)
config_f.close()

def run_script(bot, update):
    tmp_cmd = update.message.text.split(" ", 1)
    command = tmp_cmd[0].strip('/').lower()

    if re.match('^[a-z0-9]+$', command):
        for file in os.listdir('scripts/'):
            if re.match('^%s\.[a-z]+$' % command, file):
                bot.sendChatAction(chat_id=update.message.chat.id, action=ChatAction.TYPING)
                procArgs = ['scripts/' + file]
                if len(tmp_cmd) > 1:
                    procArgs.extend(tmp_cmd[1:])

                proc = subprocess.Popen(procArgs, stdout=subprocess.PIPE)
                stdout = proc.stdout

                while True:
                    # We do this to avoid buffering from the subprocess stdout
                    tmp = os.read(stdout.fileno(), 65536).strip()
                    if tmp:
                        bot.sendMessage(chat_id=update.message.chat.id, text=tmp, parse_mode=ParseMode.MARKDOWN, disable_notification=True, reply_to_message_id=update.message.message_id)
                    sys.stdout.flush()
                    if proc.poll() != None:
                        break

bot = Bot(config['telegram']['token'])
u = Updater(bot=bot)
for file in os.listdir('scripts/'):
    command = file.split('.', 1)
    u.dispatcher.addTelegramCommandHandler(command[0], run_script)
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
