import asyncio

from smsgateway.sources.commands.utils import parse_message
from smsgateway.sources.matrix_utils import init_client
from smsgateway.sources.sms import command_list
from smsgateway.sources.utils import *


def init():
    global app_log, IDENTIFIER, command_regex, client
    app_log = setup_logging("matrix-send")
    IDENTIFIER = "MX"
    command_regex = re.compile('^(?P<command>[a-zA-Z ]+)$')

    if not client:
        client = init_client()


def check(cmd, multiline):
    init()
    # print("Checking %s" % cmd)
    if cmd.lower() == IDENTIFIER.lower() and multiline:
        return True
    else:
        return False


async def send_message(message, to):
    init()
    
    await client.room_send(
        # Watch out! If you join an old room you'll see lots of old messages
        room_id=to,
        message_type="m.room.message",
        content={
            "msgtype": "m.text",
            "body": message
        }
    )
    msg = format_sms(IDENTIFIER, message, {
        'to_id': to,
        'status': 'Processed'
    })
    app_log.info(msg)
    # ret = '\n'.join([
    #   IDENTIFIER,
    #   f"To: {name}",
    #   "",
    #   message
    # ])
    return True, msg


def run(lines):
    # init()

    app_log.info("Forwarding Matrix Message")
    message, to = parse_message(lines, app_log=app_log)

    if to and message:
        loop = asyncio.get_event_loop()
        success, ret = loop.run_until_complete(send_message(message, to))
        if success:
            ret = None
        loop.close()
    else:
        ret = f"Couldn't match To: {to} or message {message}"
        app_log.error(ret)
    return ret


if __name__ == '__main__':
    init()

command_list.append({
    'name': 'MX-Forwarder',
    'check': check,
    'run': run
})
