import re, subprocess, json, os
from smsgateway.sources.sms import command_list
from smsgateway.config import *
from smsgateway import sink_sms
from smsgateway.sources.utils import *

from fbchat.models import *
from smsgateway.sources.facebook_utils import *

def check(cmd, multiline):
    global IDENTIFIER
    IDENTIFIER = "FB"

    # app_log.info("Checking %s" % cmd)
    if cmd.lower() == IDENTIFIER.lower() and multiline:
      return True
    else:
      return False


def run(lines):
    global IDENTIFIER, app_log

    IDENTIFIER = "FB"
    app_log = setup_logging("facebook-send")

    app_log.info("Forwarding Facebook Message")
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
        app_log.info("Sending Facebook msg:\n%s" % message)
        client = login(FB_CREDENTIALS, FB_COOKIE_PATH, Client)
        id = None
        name = None
        thread_type = None
        thread_list = None
        try:
            thread_list = client.fetchThreadInfo(to_matched)
        except:
            pass
        if thread_list and len(thread_list) > 0 and to_matched in thread_list:
            match = thread_list[to_matched]
            id = match.uid
            name = match.name
            thread_type = match.type
        if not id:
            user_list = client.searchForUsers(to_matched)
            if user_list and len(user_list) > 0:
                id = user_list[0].uid
                name = user_list[0].name
                thread_type = ThreadType.USER
        if not id:
            group_list = client.searchForGroups(to_matched)
            if group_list and len(group_list) > 0:
                id = group_list[0].uid
                name = group_list[0].name
                thread_type = ThreadType.GROUP

        if id != None:
            ret = f"Message to {id} ({thread_type}), called {name}:\n{message}"
            app_log.info(ret)
            client.send(Message(text=message), thread_id=id, thread_type=thread_type)
        else:
            ret = f"User/Group {to_matched} couldn't be found!"
            app_log.error(ret)
            return ret



    else:
        ret = f"Couldn't match To: {to_matched} or message {message}"
        app_log.error(ret)
    return ret

command_list.append({
    'name' : 'FB-Forwarder',
    'check': check,
    'run': run
})
