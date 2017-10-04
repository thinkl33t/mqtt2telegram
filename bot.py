#!./venv/bin/python
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

with open('config.yaml') as config_f:
    config = yaml.safe_load(config_f)

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

_announce_next_open = False
_reversed = False

def on_message(mosq, obj, msg):
    global _announce_next_open, _reversed
    if msg.topic == 'door/outer/opened/username':
        send_to_bot("*%s* opened the outer door." % msg.payload.decode('utf-8'), increment = True)
    elif msg.topic == 'door/outer/doorbell':
        _reversed = random.choice([False] * 20 + [True])
        send_to_bot("Doorbell"[::-1 if _reversed else 1], increment = True)
        _announce_next_open = True
    elif msg.topic == 'door/outer/invalidcard':
        send_to_bot("Unknown card at door", increment = True)
    elif msg.topic == 'door/outer/opened/key':
        send_to_bot("🚨 *Door opened with manual override key*")
        _announce_next_open = True
    elif msg.topic == 'bot/outgoing':
        send_to_bot(msg.payload.decode('utf-8'))
    elif msg.topic == 'door/outer/state' and msg.payload == b'opened' and _announce_next_open:
        send_to_bot("Door opened"[::-1 if _reversed else 1])
        _reversed = False
        _announce_next_open = False
    elif msg.topic == 'system/alfred_outer/state':
        if msg.payload == b'offline':
            send_to_bot("Alfred fell over 😢")
        else:
            send_to_bot("Alfred came back 😊")



mqttc = mqtt.Client(config['mqtt']['name'])

mqttc.will_set("system/%s/state" % config['mqtt']['name'], payload='offline', qos=2, retain=True)
mqttc.connect(config['mqtt']['server'])
mqttc.subscribe("door/outer/#")
mqttc.subscribe("bot/outgoing")
mqttc.subscribe("system/alfred_outer/state")
mqttc.on_message = on_message
mqttc.publish("system/%s/state" % config['mqtt']['name'], payload='online', qos=2, retain=True)
send_to_bot("I was restarted for some reason!")

mqttc.loop_forever()
