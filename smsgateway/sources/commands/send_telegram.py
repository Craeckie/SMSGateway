import asyncio, re, json
from smsgateway.sources.sms import command_list
from smsgateway.config import *
from smsgateway.sources.utils import *
from smsgateway import sink_sms
from telethon import TelegramClient, utils

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
    if isinstance(entity, User):
        return ' '.join([x for x in [entity.first_name, entity.last_name] if x])
    elif 'title' in entity:
        return entity.title
    else:
        return None

async def send_message(message, to_matched):
    print("Starting client..")
    client = TelegramClient(session_path, api_id, api_hash)
    try:
        await client.start()
    except Exception as e:
        ret = "Could not connect! Run python3 -m smsgateway.sources.commands.send_telegram to authorize!\nError: %s" % e
        app_log.error(ret)
        return ret

    to = None
    for x in await client.iter_dialogs():
        name = get_display_name(x.entity)
        if name and name == to_matched:
          to = x.entity.id
          print("Found it via display_name: %s" % x.entity.stringify())
          break
    if not to:
        print(f"Couldn't find {to}! Trying directly..")
        to = name = to_matched

    print("Sending Telegram msg:\n%s" % message)

    try:
        import getpass
        print("I am: %s" % getpass.getuser())
    except:
        pass

    await client.send_message(to, message)
    await client.disconnect()
    ret = '\n'.join([
      IDENTIFIER,
      f"To: {name}",
      "",
      message
    ])
    return ret

def run(lines):
    print("Forwarding Telegram Message")
    messageStarted = False
    to_matched = None
    message = ""

    for line in lines[1:]: # skip IDENTIFIER
        if messageStarted:
            message += f"\n{line}"
        elif not line.strip(): # empty line
            messageStarted = True
            message += line
        else:
            mTo = re.match("To: (.*)$", line)
            if mTo:
                to_matched = mTo.group(1).strip()
            else:
                app_log.warning(f"Unkown header: {line}!")

    if to_matched and message:
      loop = asyncio.get_event_loop()
      ret = loop.run_until_complete(send_message(message, to_matched))
      loop.close()
    else:
      ret = f"Couldn't match To: {to_matched} or message {message}"
      app_log.error(ret)
    return ret


if __name__ == '__main__':
    client = TelegramClient(session_path, api_id, api_hash)
    if not client.start():
        app_log.error("Could not connect! Run python3 -m smsgateway.source.telegram to authorize!")
        sys.exit(1)

command_list.append({
    'name' : 'TG-Forwarder',
    'check': check,
    'run': run
})
