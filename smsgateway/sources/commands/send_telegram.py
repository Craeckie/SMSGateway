import asyncio, re, json
from async_generator import aclosing

from smsgateway.sources.sms import command_list
from smsgateway.config import *
from smsgateway.sources.utils import *
from smsgateway import sink_sms

from telethon import TelegramClient, utils

from telethon.tl.types import Chat, User, Channel, \
  PeerUser, PeerChat, PeerChannel, \
  MessageMediaGeo, MessageMediaContact, MessageMediaPhoto, \
  MessageMediaDocument, MessageMediaWebPage, \
  Document, DocumentAttributeFilename, DocumentAttributeSticker


app_log = setup_logging("telegram-send")

IDENTIFIER = "TG"

command_regex = re.compile('^(?P<command>[a-zA-Z ]+)$')

api_id = 242101
api_hash = "80cbc97ce425aae38c1e0291ef2ab2a4"

session_path = os.path.join(CONFIG_DIR, 'telegram-send')

def check(cmd, multiline):
    # print("Checking %s" % cmd)
    if cmd.lower() == IDENTIFIER.lower() and multiline:
      return True
    else:
      return False

def get_display_name(entity):
    app_log.debug("Looking up entity " + entity.stringify())
    if isinstance(entity, User):
        return ' '.join([x for x in [entity.first_name, entity.last_name] if x])
    elif isinstance(entity, Chat) or isinstance(entity, Channel):
        return entity.title
    else:
        return None

async def send_message(message, to_matched):
    app_log.info("Starting client..")
    client = TelegramClient(session_path, api_id, api_hash)
    try:
        await client.start()
    except Exception as e:
        ret = "Could not connect! Run python3 -m smsgateway.sources.commands.send_telegram to authorize!\nError: %s" % e
        app_log.error(ret)
        return (False, ret)

    to = None
    async with aclosing(client.iter_dialogs()) as agen:
      async for x in agen:
          name = get_display_name(x.entity)
          if name and name == to_matched:
            to = x.entity.id
            app_log.info("Found it via display_name: %s" % x.entity.stringify())
            break
    if not to:
        app_log.warning(f"Couldn't find {to}! Trying directly..")
        to = name = to_matched

    app_log.info("Sending Telegram msg:\n%s" % message)

    try:
        import getpass
        app_log.info("I am: %s" % getpass.getuser())
    except:
        pass

    await client.send_message(to, message)
    await client.disconnect()
    msg = format_sms(IDENTIFIER, message, {
      'to': name,
      'status': 'Processed'
    })
    app_log.info(msg)
    # ret = '\n'.join([
    #   IDENTIFIER,
    #   f"To: {name}",
    #   "",
    #   message
    # ])
    return (True, msg)

def run(lines):
    app_log.info("Forwarding Telegram Message")
    messageStarted = False
    to_matched = None
    message = ""

    for line in lines[1:]: # skip IDENTIFIER
        if messageStarted:
            message += f"\n{line}"
        elif not line.strip(): # empty line
            messageStarted = True
        else:
            mTo = re.match("^To: (.*)$", line)
            if mTo:
                to_matched = mTo.group(1).strip()
            else:
                app_log.warning(f"Unkown header: {line}!")

    if to_matched and message:
      loop = asyncio.get_event_loop()
      (success, ret) = loop.run_until_complete(send_message(message, to_matched))
      if success:
          ret = None
      loop.close()
    else:
      ret = f"Couldn't match To: {to_matched} or message {message}"
      app_log.error(ret)
    return ret


if __name__ == '__main__':
    client = TelegramClient(session_path, api_id, api_hash)
    if not client.start():
        app_log.error("Could not connect to Telegram!\nIf you haven't authorized this client, run python3 -m smsgateway.sources.commands.send_telegram!")
        sys.exit(1)

command_list.append({
    'name' : 'TG-Forwarder',
    'check': check,
    'run': run
})
