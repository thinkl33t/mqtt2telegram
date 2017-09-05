#!/usr/bin/python
from __future__ import print_function

import time
import yaml
import os
import re
import subprocess
import logging
import random

from telegram.ext import Updater, CommandHandler
from telegram import ParseMode, ChatAction
import paho.mqtt.client as mqtt

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
                #/home/irccat/pycat/scripts/test.py pusherrobot #hacman thinkl33t ?test
                procArgs = ['scripts/' + file]
                procArgs.append("@PusherRobot")
                procArgs.append(str(update.message.chat.id))
                if update.message.from_user.username:
                    procArgs.append(update.message.from_user.username)
                else:
                    procArgs.append(update.message.from_user.first_name)

                procArgs.append(update.message.text)

                print(procArgs)

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

u = Updater(config['telegram']['token'])
for file in os.listdir('scripts/'):
    command = file.split('.', 1)
    u.dispatcher.add_handler(CommandHandler(command[0], run_script))
u.start_polling()

lastmsg = ("", 0, 2, 0) # txt, id, counter, time
def send_to_bot(message, increment=False):
    global u, config, lastmsg
    if lastmsg[0] == message and time.time() - lastmsg[3] < 60 and increment == True:
        u.bot.editMessageText(chat_id=config['telegram']['chat_id'], message_id=lastmsg[1], text="{} ({})".format(message, lastmsg[2]), parse_mode=ParseMode.MARKDOWN)
        lastmsg = (lastmsg[0], lastmsg[1], lastmsg[2] + 1, time.time())
    else:
        m = u.bot.sendMessage(chat_id=config['telegram']['chat_id'], text=message, parse_mode=ParseMode.MARKDOWN, disable_notification=True)
        lastmsg = (message, m.message_id, 2, time.time())

def on_message(mosq, obj, msg):
    if msg.topic == 'door/outer/opened/username':
        send_to_bot("*%s* opened the outer door." % msg.payload.decode('utf-8'), increment = True)
    elif msg.topic == 'door/outer/buzzer':
        send_to_bot("%s" % random.choice(['Buzzer', 'Buzzer', 'Buzzer', 'Buzzer', 'Buzzer', 'Buzzer', 'Buzzer', 'Buzzer', 'Buzzer', 'rezzuB']), increment = True)
    elif msg.topic == 'door/outer/invalidcard':
        end_to_bot("Unknown card at door", increment = True)
    elif msg.topic == 'bot/outgoing':
        send_to_bot(msg.payload.decode('utf-8'))
    elif msg.topic == 'door/shutter/state/open':
        send_to_bot("Shutter Opened!", increment = True)
    elif msg.topic == 'door/shutter/state/closed':
        send_to_bot("Shutter Closed!", increment = True)

mqttc = mqtt.Client(config['mqtt']['name'])
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
