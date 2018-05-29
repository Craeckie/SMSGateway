import sys, os
from smsgateway import sink_sms
from smsgateway.sources.utils import *
from smsgateway.config import *

from telethon import TelegramClient, events
from telethon.tl.functions.users import GetFullUserRequest

app_log = setup_logging("telegram")

IDENTIFIER = "TG"

api_id = 242101
api_hash = "80cbc97ce425aae38c1e0291ef2ab2a4"

client = TelegramClient('smsgateway', api_id, api_hash,update_workers=1, spawn_read_thread=False)
if not client.start():
    msg = "Could not connect! Run python3 -m smsgateway.source.telegram to authorize!"
    app_log.error(msg)
    print(msg)
    sys.exit(1)

msg = "Started TelegramClient"
app_log.info(msg)

@client.on(events.NewMessage())
def callback(event):

    try:
      if event.message.out:
        user_id = event.message.to_id
      else:
        user_id = event.message.from_id
      user = client(GetFullUserRequest(user_id)).user


      user_number = user.phone if user.phone else ""
      user_name = ' '.join([x for x in [user.first_name, user.last_name] if x])
      if user_number:
          user_name += " (%s)" % user_number

      if event.message.out:
          msg = "New message to %s!" % user_name
          app_log.info(msg)
      else:
          msg = "New message from %s!" % user_name
          app_log.info(msg)
      app_log.debug(msg)
    except Exception as e:
        app_log.warning(e)

msg = "Listening to messages.."

app_log.info(msg)

client.idle()
