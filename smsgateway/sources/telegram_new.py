import sys, os, signal, traceback
from smsgateway import sink_sms
from smsgateway.sources.utils import *
from smsgateway.config import *

from telethon import TelegramClient, events
from telethon.tl.types import Chat, User, Channel, \
  MessageMediaGeo, MessageMediaContact, MessageMediaPhoto, \
  MessageMediaDocument, MessageMediaWebPage, \
  Document, DocumentAttributeFilename, DocumentAttributeSticker
from telethon.tl.functions.users import GetFullUserRequest

app_log = setup_logging("telegram")

IDENTIFIER = "TG"

api_id = 242101
api_hash = "80cbc97ce425aae38c1e0291ef2ab2a4"

session_path = os.path.join(CONFIG_DIR, 'telegram')
client = TelegramClient(session_path, api_id, api_hash,update_workers=1, spawn_read_thread=False)
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
        webpage = media.webpage
        msg += "Media: Webpage\n"
        msg += f"> {webpage.site_name}\n> {webpage.title}\n> {webpage.description}\n\n"
    else:
        msg += "Media: Unknown"
    return msg

def get_user_info(entity):
    info = {}
    if isinstance(entity, User):
      #user = client(GetFullUserRequest(user_id)).user
      if entity.phone:
          info['phone'] = entity.phone
      info['name'] = ' '.join([x for x in [entity.first_name, entity.last_name] if x])
      # if user_number:
      #     user_name += " (%s)" % user_number
    return info

def get_chat_info(id):
    entity = client.get_entity(id)
    info = {}
    if isinstance(entity, Chat):
        info['group'] = entity.title
    elif isinstance(entity, Channel):
        info['channel'] = entity.title
    return info
def get_channel_info(entity):
    info = {}
    return info

@client.on(events.NewMessage())
@client.on(events.MessageEdited())
def callback(event):
    try:
      if event.message.out:
        user_id = event.message.to_id
      else:
        user_id = event.message.from_id

      chat_info = {'ID': event.message.id}

      user_entity = client.get_entity(user_id)
      user_info = get_user_info(user_entity)
      if 'name' in user_info:
        chat_info['to' if event.message.out else 'from'] = user_info['name']
      if 'phone' in user_info:
        chat_info['phone'] = user_info['phone']

      group_info = get_chat_info(event.message.to_id)
      if group_info:
        # if event.message.out: # if sent to group/channel, get name
        for key in ['group', 'channel']:
          if key in group_info:
              chat_info['group'] = group_info[key]
              if event.message.out:
                  chat_info['to'] = group_info[key]
        # else: # from someone else
        #     chat_info['from'] =
      # if isinstance(group_entity, Chat):
      #     chat_info['group'] = group_entity.title
      #     if event.message.out:
      #         user_name = chat_info['group']
      # elif isinstance(group_entity, Channel):
      #     chat_info['channel'] = group_entity.title
      #     if event.message.out:
      #         user_name = chat_info['channel']
      if event.message.edit_date:
          chat_info['edit'] = "True"
      msg = ""

      if event.message.fwd_from:
          fwd_from = event.message.fwd_from
          if fwd_from.from_id:
              user_info = get_user_info(from_id)
          elif fwd_from.channel_id:
              user_info = get_chat_info(fwd_from.channel_id)
          msg += f"Forwarded from {user_info['name']}:\n"
          # if 'name' in user_info:
          #   chat_info['from_name'] = user_info['name']
          # if 'phone' in user_info:
          #   chat_info['from_phone'] = user_info['phone']

      # if event.message.reply_to_msg_id:
      #     for message in client.iter_messages('username', limit=10):
      msg += event.message.message

      media = event.message.media
      if media:
          msg = parseMedia(media, msg)

      if event.message.out:
          app_log.info("New message to %s!" % chat_info['to'])
          sink_sms.send_dict(IDENTIFIER, msg, chat_info)
          # sink_sms.send_from_me(IDENTIFIER, msg, chat_info['to'])
      else:
          app_log.info("New message from %s!" % chat_info['from'])
          sink_sms.send_dict(IDENTIFIER, msg, chat_info)
          # sink_sms.send(IDENTIFIER, msg, user_name, user_number, group_name)
      app_log.debug(msg)
    except Exception as e:
        app_log.warning(traceback.format_exc())
        app_log.warning(event.stringify())

app_log.info("Catching up..")

def handler(signum, frame):
    if signum == signal.SIGALRM:
      app_log.info("Got a signal for timeout, raising exception")
      raise Exception("Function timed out!")
signal.signal(signal.SIGALRM, handler)
signal.alarm(10)
try:
    client.catch_up()
except Exception as e:
    app_log.warning("client.catch_up failed with Exception: %s" % e)
signal.alarm(0)

app_log.info("Listening to messages..")

client.idle()
