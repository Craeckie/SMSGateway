import asyncio, sys, os, signal, traceback
from async_generator import aclosing
from smsgateway import sink_sms
from smsgateway.sources.utils import *
from smsgateway.config import *

from telethon import TelegramClient, events
from telethon.tl.types import Chat, User, Channel, \
  PeerUser, PeerChat, PeerChannel, \
  MessageMediaGeo, MessageMediaContact, MessageMediaPhoto, \
  MessageMediaDocument, MessageMediaWebPage, \
  Document, DocumentAttributeFilename, DocumentAttributeSticker
from telethon.tl.functions.users import GetFullUserRequest

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


def parseMedia(media, msg):
    if msg:
        msg += "\n"
    if isinstance(media, MessageMediaGeo):
        geo = media.geo
        msg += f"https://osmand.net/go?lat={geo.lat}&lon={geo.long}&z=15"
    elif isinstance(media, MessageMediaPhoto):
        photo = media.photo
        msg += "Media: Photo"
        if photo.sizes:
            largest = [s for s in photo.sizes if s.type == 'y']
            if len(largest) >= 1:
                largest = largest[0]
                msg += f" ({largest.w}x{largest.h})"
    elif isinstance(media, MessageMediaContact):
        msg += "Media: Contact\n"
        if media.first_name or media.last_name:
            msg += f"Name:"
            if media.first_name:
                msg += f" {media.first_name}"
            if media.last_name:
                msg += f" {media.last_name}"
            msg += "\n"
        if media.phone_number:
            msg += f"Phone: {media.phone_number}"
    elif isinstance(media, MessageMediaDocument):
        document = media.document
        filename = None
        if document.attributes:
            filename = [attr.file_name for attr in document.attributes if isinstance(attr, DocumentAttributeFilename)]
            if len(filename) > 0:
                filename = filename[0]
        if isinstance(document, Document) and document.mime_type == "image/webp":
            msg += "Sticker"
            alt_smiley = [attr.alt for attr in document.attributes if isinstance(attr, DocumentAttributeSticker)]
            if len(alt_smiley) > 0:
                msg += f": {alt_smiley[0]}"
            msg += "\n"
        else:
          msg += "Media: "
          if document.mime_type.startswith("video"):
              if filename == "giphy.mp4":
                msg += "GIF\n"
              else:
                msg += "Video\n"
          else:
              msg += "Media: File\n"
          if filename:
            msg += f"Filename: {filename}\n"
          if document.size:
              size = sizeof_fmt(document.size)
              msg += f"Size: {size}\n"
    elif isinstance(media, MessageMediaWebPage):
        msg += "Media: Webpage"
        webpage = media.webpage
        items = ['site_name', 'title', 'description']
        if isinstance(webpage, MessageMediaWebPage): #all(item in webpage for item in items):
          msg += "\n" + '\n'.join("> " + [webpage[item] for item in items])
    else:
        msg += "Media: Unknown"
    return msg

def get_user_info(entity):
  user_name = None
  user_phone = None
  if entity.phone:
      user_phone = entity.phone
  user_name = ' '.join([x for x in [entity.first_name, entity.last_name] if x])
  return (user_name, user_phone)

async def get_entity(input_id):
    try:
      input_entity = await client.get_input_entity(input_id) if input_id else None
    except:
      pass
    entity = await client.get_entity(input_entity) if input_entity else None
    if not entity:
        entity = await client.get_entity(input_id) if input_id else None
    return entity

#@asyncio.coroutine
async def get_outgoing_info(id):
    info = {}
    entity = await get_entity(id)
    if isinstance(entity, User):
      (name, phone) = get_user_info(entity)
      if name:
          info['to'] = name
      if phone:
          info['phone'] = phone
      info['type'] = 'User'
    elif isinstance(entity, Chat):
        info['to'] = entity.title
        info['type'] = 'Group'
    elif isinstance(entity, Channel):
        info['to'] = entity.title
        info['type'] = 'Channel'
    else:
        app_log.warning(f"Unknown entity type for id {id}:\nEntity: {entity.stringify()}")
    return info

# @asyncio.coroutine
async def get_incoming_info(from_id, to_id):
    from_entity = await get_entity(from_id)
    to_entity = await get_entity(to_id)
    info = {}
    if from_entity:
      if isinstance(from_entity, User):
        (name, phone) = get_user_info(from_entity)
        if name:
            info['from'] = name
        if phone:
            info['phone'] = phone
        info['type'] = 'User'
      elif isinstance(from_entity, Channel):
        info['from'] = from_entity.title
        info['type'] = 'Channel'
      else:
          app_log.warning(f"Unknown entity type for id {from_id}!")
    if to_entity:
      if isinstance(to_entity, Chat):
          info['to'] = to_entity.title
          info['type'] = 'Group'
      elif isinstance(to_entity, Channel):
        info['to'] = to_entity.title
        info['type'] = 'Channel'
      else:
          app_log.warning(f"Unknown entity type for id {to_id}!")
    return info

async def get_chat_id(out, from_id, to_id):
    entity = await client.get_entity(to_id) if to_id else None
    if isinstance(entity, Chat) or isinstance(entity, Channel):
        return entity.id
    elif out and entity:
        return entity.id
    else:
        entity = await client.get_entity(from_id) if from_id else None
    if entity:
        return entity.id
    else:
        return None

@client.on(events.NewMessage())
@client.on(events.MessageEdited())
async def callback(event):
    chat_info = {'ID': event.message.id}
    try:
      if event.message.out:
          if not event.message.to_id:
              raise Exception("No to_id given, but messsage is going out!")
          chat_info.update(await get_outgoing_info(event.message.to_id))
      else: #in
          chat_info.update(await get_incoming_info(event.message.from_id, event.message.to_id))

      if event.message.edit_date:
          chat_info['edit'] = "True"
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
              entity = await client.get_entity(fwd_from.channel_id)
              user_info['name'] = entity.title
          if 'name' in user_info:
              msg += f"Forwarded from {user_info['name']}:\n"

      if event.message.reply_to_msg_id:
        chat_id = await get_chat_id(event.message.out, event.message.from_id, event.message.to_id)
        if chat_id:
          reply_info = None
          async with aclosing(client.iter_messages(chat_id)) as agen:
            async for m in agen:
                if m.id == event.message.reply_to_msg_id:
                    name = None
                    if m.from_id:
                      print(f"from: {m.from_id}")
                    if m.to_id:
                      print(f"to: {m.to_id}")
                    if m.out:
                        reply_info = await get_incoming_info(m.from_id, m.to_id)
                        if 'from' in reply_info:
                          name = reply_info['from']
                    if not m.out or not name:
                        reply_info = await get_outgoing_info(m.from_id)
                        if 'to' in reply_info:
                          name = reply_info['to']
                    if not name:
                        name = "N/A"
                    msg += f"Reply to {name}:\n"
                    msg += '\n'.join(["> " + line for line in m.message.split('\n')])
                    msg += "\n\n"
                    break
          if not reply_info:
              app_log.warning(f"No message found for reply_to_msg_id {event.message.reply_to_msg_id} in chat {chat_id}!")
              msg += f"Reply to unknown message"
        else:
          app_log.warning("Reply with unknown chat_id!");
          msg += f"Reply to unknown message"

         #for message in client.iter_messages('username', limit=10):
      msg += event.message.message

      media = event.message.media
      if media:
          msg = parseMedia(media, msg)

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
        app_log.warning(traceback.format_exc())
        app_log.warning(event.stringify())
        app_log.warning(str(chat_info))

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
        app_log.warning("client.catch_up failed with Exception: %s" % e)
        app_log.warning(traceback.format_exc())
    # signal.alarm(0)

    app_log.info("Listening to messages..")

    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
