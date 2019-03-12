import asyncio

from telethon import TelegramClient
from telethon.tl.types import Chat, User, Channel

from smsgateway.sources.sms import command_list
from smsgateway.sources.utils import *
from .utils import parse_message


def init():
    global app_log, IDENTIFIER, command_regex, api_id, api_hash, session_path
    app_log = setup_logging("telegram-send")
    IDENTIFIER = "TG"
    command_regex = re.compile('^(?P<command>[a-zA-Z ]+)$')

    api_id = 242101
    api_hash = "80cbc97ce425aae38c1e0291ef2ab2a4"

    session_path = os.path.join(CONFIG_DIR, 'telegram-send')


def check(cmd, multiline):
    init()
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


async def send_message(data):
    app_log.info("Starting client..")
    client = TelegramClient(session_path, api_id, api_hash)
    try:
        await client.start()
    except Exception as e:
        ret = "Could not connect! Run python3 -m smsgateway.sources.commands.send_telegram to authorize!\nError: %s" % e
        app_log.error(ret)
        return (False, ret)

    to = name = phone = None
    if 'phone' in data:
        phone = to = data['phone']
        # TODO: use get_entity from telegram_utils. Try next method, if fails
    else:
        async for x in client.iter_dialogs():
            name = get_display_name(x.entity)
            if name and name == data['to'] and not to:
                to = x.entity.id
                app_log.info("Found it via display_name: %s" % x.entity.stringify())
                break
    if not to:
        app_log.warning(f"Couldn't find {to}! Trying directly..")
        to = name = data['to']

    app_log.info("Sending Telegram msg:\n%s" % data['message'])

    # try:
    #     import getpass
    #     app_log.info("I am: %s" % getpass.getuser())
    # except:
    #     pass

    await client.send_message(to, data['message'])

    await client.disconnect()
    sendData = {'status': 'Processed', 'to': name if name else phone}
    if phone:
        sendData['phone'] = phone
    msg = format_sms(IDENTIFIER, data['message'], sendData)
    app_log.info(msg)
    # ret = '\n'.join([
    #   IDENTIFIER,
    #   f"To: {name}",
    #   "",
    #   message
    # ])
    return (True, msg)


def run(lines):
    init()

    data = parse_message(app_log, lines)
    if data['success']:
        loop = asyncio.get_event_loop()
        (success, ret) = loop.run_until_complete(send_message(data))
        if success:
            ret = None
        loop.close()
    else:
        ret = data['error']
    return ret


def authorize():
    client = TelegramClient(session_path, api_id, api_hash)
    if not client.start():
        app_log.error(
            "Could not connect to Telegram!\nIf you haven't authorized this client, run python3 -m "
            "smsgateway.sources.commands.send_telegram!")
        sys.exit(1)


if __name__ == '__main__':
    init()
    authorize()

command_list.append({
    'name': 'TG-Forwarder',
    'check': check,
    'run': run
})
