import json
import time, asyncio
from smsgateway import sink_sms
from smsgateway.config import *
from smsgateway.sources.utils import *

from slackclient import SlackClient

def init():
    global IDENTIFIER, app_log
    IDENTIFIER = "SL"
    app_log = setup_logging("slack")

def main():
    init()

    sc = SlackClient(SL_TOKEN)
    
    data = sc.api_call("users.list")
    users = {}
    app_log.info("Getting users..")
    if not data['ok']:
        app_log.error("Could not get user information!")
        app_log.error(f"Token: {SL_TOKEN}")
        app_log.error(data)
        return
    for u in data['members']:
        uID = u['id']
        uName = None
        if 'real_name' in u:
            uName = u['real_name']
        else:
            if 'profile' in u:
                p = u['profile']
                if 'real_name' in p:
                    uName = p['real_name']
        if not uName:
            app_log.warning(f'Could not get real_name of {uID}:')
            app_log.warning(json.dumps(u, indent=2))
            continue
        app_log.debug(f"{uID}: {uName}")
        users[uID] = uName
    app_log.info(f"Got {len(users)} users")

    app_log.info("Getting channels..")
    data = sc.api_call("channels.list")
    channels = {}
    if not data['ok']:
        app_log.error("Could not get channel information!")
        app_log.error(f"Token: {SL_TOKEN}")
        app_log.error(data)
        return
    for u in data['channels']:
        uID = u['id']
        uName = u['name']
        app_log.debug(f"{uID}: {uName}")
        channels[uID] = uName
    app_log.info(f"Got {len(channels)} channels")


    if not sc.rtm_connect(auto_reconnect=True):
        app_log.error("Could not connect to Slack!")
        return False

    while True:
        data = sc.rtm_read()
        if data:
            for entry in data:
                app_log.debug(entry)
                type = entry['type']
                if type == 'message':
                    text = None
                    if 'message' in entry:
                        msg = entry['message']
                        isInChannel = True
                        app_log.info("Got a message in a channel!")
                    elif 'text' in entry:
                        msg = entry
                        isInChannel = False
                        app_log.info("Got a message from a user/bot!")
                    else:
                        app_log.warning("Could not parse this:\n" + entry)
                        continue
                    if not msg['text']:
                        print("Has no message!")
                        continue
                    else:
                        text = msg['text']
                        user = users[msg['user']]
                        chat_info = {
                            'date': str(int(float(msg['ts']))),
                            'from': user
                        }
                        if 'client_msg_id' in msg:
                            chat_info['ID'] = msg['client_msg_id']
                        if isInChannel:
                            channel = channels[entry['channel']]
                            chat_info.update({
                              'type': 'Group',
                              'to': channel,
                            })
                        sink_sms.send_dict(IDENTIFIER, text, chat_info)

        time.sleep(1)



if __name__ == '__main__':
    main()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
