import asyncio, sys, os, signal, traceback
from smsgateway import sink_sms
from smsgateway.sources.utils import *
from smsgateway.config import *

from telethon import TelegramClient, events
from telethon.tl.types import Chat, User, Channel, \
                              PeerUser, PeerChat, PeerChannel
from telethon.tl.functions.users import GetFullUserRequest

from smsgateway.sources.telegram_utils import *

app_log = setup_logging("telegram")

IDENTIFIER = "TG"

api_id = 242101
api_hash = "80cbc97ce425aae38c1e0291ef2ab2a4"
session_path = os.path.join(CONFIG_DIR, 'telegram')

client = TelegramClient(session_path, api_id, api_hash) #,update_workers=1, spawn_read_thread=False)
if not client.start():
    app_log.error("Could not connect! Run python3 -m smsgateway.sources.telegram to authorize!")
    sys.exit(1)

app_log.info("Started TelegramClient")


@client.on(events.NewMessage())
@client.on(events.MessageEdited())
async def callback(event):
    chat_info = {'ID': event.message.id}
    try:
      if event.message.out:
          if not event.message.to_id:
              raise Exception("No to_id given, but messsage is going out!")
          chat_info.update(await get_outgoing_info(client, app_log, event.message.to_id))
      else: #in
          chat_info.update(await get_incoming_info(client, app_log, event.message.from_id, event.message.to_id))

      if event.message.edit_date:
          chat_info['edit'] = "True"
      if event.message.date:
          chat_info['date'] = event.message.date.strftime('%s')
      msg = ""

      if event.message.fwd_from:
          fwd_from = event.message.fwd_from
          user_info = {}
          if fwd_from.from_id:
              entity = await client.get_entity(fwd_from.from_id)
              (name, phone) = get_user_info(entity)
              if name:
                  user_info['name'] = name
          elif fwd_from.channel_id:
              entity = await client.get_entity(client, fwd_from.channel_id)
              user_info['name'] = entity.title
          if 'name' in user_info:
              msg += f"Forwarded from {user_info['name']}:\n"

      if event.message.reply_to_msg_id:
          try:
            msg += await parseReplyTo(client, app_log, event)
          except Exception as e:
            msg += f"Reply parsing failed: {e}\n\n"
            app_log.warning(e, exc_info=True)
            app_log.warning(event.stringify())

      if event.message.reply_markup:
          try:
            chat_info.update(parseButtons(event.message.reply_markup))
          except Exception as e:
            msg += f"Button parsing failed: {e}\n\n"
            app_log.warning(e, exc_info=True)
            app_log.warning(event.stringify())


      msg += event.message.message

      media = event.message.media
      if media:
          if msg:
              msg += "\n"
          try:
            msg += parseMedia(media)
          except Exception as e:
            msg += f"Media parsing failed: {e}"

      if event.message.out:
          if 'to' in chat_info:
            app_log.info("New message to %s!" % chat_info['to'])
          sink_sms.send_dict(IDENTIFIER, msg, chat_info)
          # sink_sms.send_from_me(IDENTIFIER, msg, chat_info['to'])
      else:
          if 'from' in chat_info:
            app_log.info("New message from %s!" % chat_info['from'])
          sink_sms.send_dict(IDENTIFIER, msg, chat_info)
          # sink_sms.send(IDENTIFIER, msg, user_name, user_number, group_name)
      app_log.debug(msg)
    except Exception as e:
        event = event.stringify()
        trace = traceback.format_exc()
        app_log.warning(event, exc_info=True)
        app_log.warning(str(chat_info))
        sink_sms.send_notif("Telegram message parsing failed!\n%s" % '\n'.join([event, trace, str(chat_info)]))

@client.on(events.MessageDeleted())
async def callback_delete(event):
    ids = event.deleted_ids
    app_log.info("Deleted messages with IDs %s!" % str(ids))
    for id in ids:
        sink_sms.send_dict(IDENTIFIER, None, {
          'ID': id,
          'Status': 'deleted'
        })

async def main():
    app_log.info("Catching up..")

    # def handler(signum, frame):
    #     if signum == signal.SIGALRM:
    #       app_log.info("Got a signal for timeout, raising exception")
    #       raise Exception("Function timed out!")
    # signal.signal(signal.SIGALRM, handler)
    # signal.alarm(10)
    try:
        await asyncio.wait_for(client.catch_up(), timeout=15)
    except Exception as e:
        app_log.warning("client.catch_up failed with Exception: %s" % e, exc_info=True)
    # signal.alarm(0)

    app_log.info("Listening to messages..")

    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
