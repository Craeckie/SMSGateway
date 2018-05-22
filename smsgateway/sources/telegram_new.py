import sys
from smsgateway import sink_sms
from smsgateway.sources.utils import *
from smsgateway.config import *

from telethon import TelegramClient, events
from telethon.tl.functions.users import GetFullUserRequest

import logging
from logging.handlers import RotatingFileHandler
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
logFile = os.path.join(LOG_DIR, 'telegram.log')
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.DEBUG)
app_log = logging.getLogger('root')
app_log.setLevel(logging.DEBUG)
app_log.addHandler(my_handler)

IDENTIFIER = "TG"

api_id = 242101
api_hash = "80cbc97ce425aae38c1e0291ef2ab2a4"

client = TelegramClient('smsgateway', api_id, api_hash,update_workers=1, spawn_read_thread=False)
if not client.start():
    print("Could not connect! Run python -m smsgateway.source.telegram to authorize!")
    sys.exit(1)

@client.on(events.NewMessage())
def callback(event):
    try:
      if event.Message.out:
        user_id = event.message.to_id
      else:
        user_id = event.message.from_id
      user = client(GetFullUserRequest(user_id)).user


      user_number = user.phone if user.phone else ""
      user_name = ' '.join([x for x in [user.first_name, user.last_name] if x])
      if user_number:
          user_name += " (%s)" % user_number

      if event.Message.out:
          print("New message to %s:" % user_name)
      else:
          print("New message from %s:" % user_name)
      print(event.message.message)
    except Exception as e:
        print(e)

client.idle()
