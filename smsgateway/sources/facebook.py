import os
from fbchat import Client
from fbchat.models import *
from smsgateway import sink_sms
from smsgateway.config import *
from smsgateway.sources.utils import *
from smsgateway.sources.facebook_utils import *

IDENTIFIER = "FB"

app_log = setup_logging("facebook")

# Subclass fbchat.Client and override required methods
class EchoBot(Client):
    def onMessage(self, mid, author_id, message, thread_id, thread_type, ts, metadata, msg, **kwargs):
        self.markAsDelivered(author_id, thread_id)
#        self.markAsRead(author_id)

        app_log.info("Message from {} in {} ({}): {}".format(author_id, thread_id, thread_type.name, message))
        source_name = author_id
        chat_info = {'ID' : mid}

        # If you're not the author, echo
        if author_id == self.uid:
            author_id = thread_id
            source_name = author_id
            isSent = True
        else:
            isSent = False

        for u in users:
            if str(u.uid) == str(author_id):
                source_name = u.name
                break
        if isSent:
            chat_info['To'] = source_name
        else:
            chat_info['From'] = source_name

        if thread_type == ThreadType.USER:
            chat_info['Type'] = 'User'
        elif thread_type == ThreadType.GROUP:
            chat_info['Type'] = 'Group'
        elif thread_type == ThreadType.ROOM:
            chat_info['Type'] = 'Channel'

        sink_sms.send_dict(IDENTIFIER, message, chat_info)
        app_log.info("Message sent by {name} to a {type} with ID {id}:\n{msg}".format(
            name='me' if isSent else source_name,
            type=chat_info['Type'],
            id=mid,
            msg=message
        ))

        # if isSent:
        #     print("To: %s\n\n%s\n" % (source_name, message))
        #     sink_sms.send_from_me(IDENTIFIER, message, source_name)
        # else:
        #     print("From: %s\n\n%s\n" % (source_name, message))
        #     sink_sms.send(IDENTIFIER, message, source_name)
#            self.sendMessage(message, thread_id=thread_id, thread_type=thread_type)

client = login(FB_CREDENTIALS, FB_COOKIE_PATH, EchoBot)

users = client.fetchAllUsers()

client.listen()
