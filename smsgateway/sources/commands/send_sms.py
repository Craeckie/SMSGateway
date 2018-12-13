import re, subprocess
from smsgateway.sources.sms import command_list
from smsgateway.config import *
from smsgateway import sink_sms

command_regex = re.compile('^(?P<command>[a-zA-Z ]+)$')

def check(cmd, multiline):
    # print("Checking %s" % cmd)
    if cmd.lower() == 'sms' and multiline:
      return True
    else:
      return False


def run(lines):
    global IDENTIFIER, app_log

    IDENTIFIER = "SMS"
    app_log = setup_logging("sms-send")

    app_log.info("Forwarding SMS")
    toL = lines[1]
    m = re.match("To: ([0-9 +]+)", toL)
    if m:
      to = m.group(1).replace(' ', '')
      app_log.info("Matched To: %s" % to)
      msg = '\n'.join(lines[2:])
      app_log.debug("Sending SMS:\n%s" % msg)
      sink_sms.send_to(to, msg)
      ret = "Sent SMS to %s!" % to
    else:
      ret = "Couldn't match To: %s" % to
      app_log.error(ret)
    return ret

command_list.append({
    'name' : 'SMS-Forwarder',
    'check': check,
    'run': run
})
