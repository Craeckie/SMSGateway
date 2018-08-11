import asyncio, json
from datetime import datetime, timedelta
from async_generator import aclosing
from telethon.tl.types import Chat, User, Channel, \
  PeerUser, PeerChat, PeerChannel, \
  MessageMediaGeo, MessageMediaGeoLive, MessageMediaContact, MessageMediaPhoto, \
  MessageMediaDocument, MessageMediaWebPage, \
  Document, DocumentAttributeFilename, DocumentAttributeSticker, DocumentAttributeAudio, \
  ReplyKeyboardHide

from smsgateway.sources.utils import *

def parseMedia(media):
    msg = ""

    if isinstance(media, MessageMediaGeo) or isinstance(media, MessageMediaGeoLive):
        geo = media.geo
        if isinstance(media, MessageMediaGeo):
          msg += "Media: geo\n"
        elif isinstance(media, MessageMediaGeoLive):
          msg += "Media: geo live\n"
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
        duration = None
        if document.attributes:
            for attr in document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                  filename = attr.file_name
                  # if len(filename) > 0:
                  #    filename = filename[0]
                elif isinstance(attr, DocumentAttributeAudio):
                  duration = attr.duration
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
          elif document.mime_type.startswith("audio"):
              msg += "Audio\n"
          else:
              msg += "File\n"
          if filename:
            msg += f"Filename: {filename}\n"
          if duration:
            duration = str(timedelta(seconds=duration))
            msg += f"Duration: {duration}\n"
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

def parseButtons(reply_markup):
    # if isinstance(reply_markup, ReplyKeyboard..)
    if isinstance(reply_markup, ReplyKeyboardHide):
      return {}
    rows = reply_markup.rows
    data_rows = []
    for row in rows:
        data_row = []
        for button in row.buttons:
            data_row.append(str(button.text))
        data_rows.append(data_row)
    return {'buttons': json.dumps(data_rows)}

def get_user_info(entity):
    user_name = None
    user_phone = None
    if entity.phone:
        user_phone = entity.phone
    user_name = ' '.join([x for x in [entity.first_name, entity.last_name] if x])
    return (user_name, user_phone)

async def get_entity(client, input_id):
    input_entity = None
    try:
      input_entity = await client.get_input_entity(input_id) if input_id else None
    except:
      pass
    entity = await client.get_entity(input_entity) if input_entity else None
    if not entity:
        entity = await client.get_entity(input_id) if input_id else None
    return entity

#@asyncio.coroutine
async def get_outgoing_info(client, app_log, id):
    info = {}
    entity = await get_entity(client, id)
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
async def get_incoming_info(client, app_log, from_id, to_id):
    from_entity = await get_entity(client, from_id)
    to_entity = await get_entity(client, to_id)
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

async def get_chat_id(client, out, from_id, to_id):
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

async def parseReplyTo(client, app_log, event):
    msg = ""
    chat_id = await get_chat_id(client, event.message.out, event.message.from_id, event.message.to_id)
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
                    reply_info = await get_incoming_info(client, app_log, m.from_id, m.to_id)
                    if 'from' in reply_info:
                      name = reply_info['from']
                if not m.out or not name:
                    reply_info = await get_outgoing_info(client, app_log, m.from_id)
                    if 'to' in reply_info:
                      name = reply_info['to']
                if not name:
                    name = "N/A"
                msg += f"Reply to {name}:\n"
                msg += '\n'.join(["> " + line for line in m.message.split('\n')])
                break
      if not reply_info:
          app_log.warning(f"No message found for reply_to_msg_id {event.message.reply_to_msg_id} in chat {chat_id}!")
          msg += f"Reply to unknown message"
    else:
      app_log.warning("Reply with unknown chat_id!");
      msg += f"Reply to unknown message"
    msg += "\n\n"
    return msg
