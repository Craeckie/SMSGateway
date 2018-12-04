
from smsgateway.config import *

import time

from slackclient import SlackClient

sc = SlackClient(SL_TOKEN)

def main():
    if not sc.rtm_connect(auto_reconnect=True):
        print("Could not connect to Slack!")
        return False

    while True:
        data = sc.rtm_read()
        if data:
          print(data)
        time.sleep(1)



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
