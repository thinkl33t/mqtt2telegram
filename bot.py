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

bot = Bot(config['telegram']['token'])
u = Updater(bot=bot)
for file in os.listdir('scripts/'):
    command = file.split('.', 1)
    u.dispatcher.addTelegramCommandHandler(command[0], run_script)
u.start_polling()

def send_to_bot(message):
    global bot, config
    bot.sendMessage(chat_id=config['telegram']['chat_id'], text=message, parse_mode=ParseMode.MARKDOWN, disable_notification=True)
    
_someone_waiting_outside = False
def on_message(mosq, obj, msg):
    global _someone_waiting_outside
    if msg.topic == 'door/outer/opened/username':
        send_to_bot("*%s* opened the outer door." % msg.payload)
    elif msg.topic == 'door/outer/buzzer':
        polarity = random.choice([1, 1, 1, 1, 1, 1, 1, 1, 1, -1])
        send_to_bot("Buzzer"[::polarity])
        _someone_waiting_outside = True if polarity > 0 else polarity
    elif msg.topic == 'door/outer/invalidcard':
        send_to_bot("Unknown card at door")
    elif msg.topic == 'bot/outgoing':
        send_to_bot(msg.payload)
    elif msg.topic == 'door/shutter/state/open':
        send_to_bot("Shutter Opened!")
    elif msg.topic == 'door/shutter/state/closed':
        send_to_bot("Shutter Closed!")
    elif msg.topic == 'door/outer' and msg.payload == 'opened' and _someone_waiting_outside:
        send_to_bot("Door opened"[::_someone_waiting_outside])
        _someone_waiting_outside = False

mqttc = mosquitto.Mosquitto(config['mqtt']['name'])
while True:
    mqttc.connect(config['mqtt']['server'])
    mqttc.subscribe("door/outer")
    mqttc.subscribe("door/outer/#")
    mqttc.subscribe("bot/outgoing")
    mqttc.subscribe("door/shutter/state/#")
    mqttc.on_message = on_message

    while mqttc.loop(0.1) == 0:
        pass
    print ("MQTT connection lost!")
    mqttc.disconnect()
    time.sleep(5)
