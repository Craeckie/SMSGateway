import re, subprocess, json, os
from smsgateway.sources.sms import command_list
from smsgateway.config import *
from smsgateway import sink_sms
from smsgateway.sources.utils import *

import logging
from logging.handlers import RotatingFileHandler

def init():
    global app_log, command_regex

    app_log = setup_logging("signal-send")

    command_regex = re.compile('^(?P<command>[a-zA-Z ]+)$')


def check(cmd, multiline):
    init()
    # app_log.info("Checking %s" % cmd)
    if cmd.lower() == 'sg' and multiline:
      return True
    else:
      return False


def run(lines):
    init()

    app_log.info("Forwarding Signal Message")
    message = ""
    messageStarted = False
    to = None
    for line in lines[1:]: # skip IDENTIFIER
        if messageStarted:
            if message:
                message += "\n"
            message += f"{line}"
        elif not line.strip(): # empty line
            messageStarted = True
        else:
            mTo = re.match("^To: (.*)$", line)
            if mTo:
                to = mTo.group(1).strip()
            else:
                app_log.warning(f"Unkown header: {line}!")
    #toL = lines[1]
    #m = re.match("To:? (.*)$", toL)
    if to:
      #to = m.group(1).replace(' ', '')
      #app_log.info("Matched To: %s" % to)
      #msg = '\n'.join(lines[2:])

      app_log.info("Sending Signal msg:\n%s" % message)
      try:
          args = [SIGNAL_CLI_PATH, '-u', SIGNAL_NUMBER, 'send', '-m', message, to]
          app_log.info("Calling %s" % str(args))
          res = subprocess.call(args, timeout=30000)
      except subprocess.TimeoutExpired as e:
          msg = "Timeout when sending SG to %s: %s" % (to, e)
          app_log.error(msg)
          return msg
      except subprocess.CalledProcessError as e:
          msg = "Failed to send SG to %s: %s" % (to, e.output)
          app_log.error(msg)
          return msg
      if res == 0:
          ret = "Sent SG to %s!" % to
      else:
          ret = "Failed to send SG to %s!" % to
    else:
      ret = "Couldn't match To: %s" % '\n'.join(lines)
      app_log.info(ret)
    return ret

command_list.append({
    'name' : 'SG-Forwarder',
    'check': check,
    'run': run
})
