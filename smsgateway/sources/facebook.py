import os
from fbchat import log, Client
from smsgateway import sink_sms
from smsgateway.config import *

IDENTIFIER = "FB"

# Subclass fbchat.Client and override required methods
class EchoBot(Client):
    def onMessage(self, author_id, message, thread_id, thread_type, **kwargs):
        self.markAsDelivered(author_id, thread_id)
        self.markAsRead(author_id)

        log.info("Message from {} in {} ({}): {}".format(author_id, thread_id, thread_type.name, message))

        # If you're not the author, echo
        if author_id != self.uid:
            source_name = author_id
            for u in users:
                if str(u.uid) == str(author_id):
                    source_name = u.name
                    break

            print("From: %s\n\n%s\n" % (source_name, message))
            sink_sms.send(IDENTIFIER, message, source_name)
#            self.sendMessage(message, thread_id=thread_id, thread_type=thread_type)

session_cookies = None
if os.path.exists(FB_COOKIE_PATH):
    with open(FB_COOKIE_PATH, 'r') as f:
         session_cookies = f.read()

client = EchoBot(FB_CREDENTIALS[0], FB_CREDENTIALS[1], session_cookies=session_cookies)
session_cookies = client.getSession()
with open(FB_COOKIE_PATH, 'w') as f:
    f.write(str(session_cookies))
    #f.write(json.dumps(session_cookies))

users = client.fetchAllUsers()

client.listen()
