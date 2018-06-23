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
    print("Forwarding SMS")
    toL = lines[1]
    m = re.match("To: ([0-9 +]+)", toL)
    if m:
      to = m.group(1).replace(' ', '')
      print("Matched To: %s" % to)
      msg = '\n'.join(lines[2:])
      print("Sending SMS:\n%s" % msg)
      sink_sms.send_to(to, msg)
      ret = "Sent SMS to %s!" % to
    else:
      ret = "Couldn't match To: %s" % to
      print(ret)
    return ret

command_list.append({
    'name' : 'SMS-Forwarder',
    'check': check,
    'run': run
})
