import re, subprocess, json, os
from smsgateway.sources.sms import command_list
from smsgateway.config import *
from smsgateway import sink_sms

import logging
from logging.handlers import RotatingFileHandler


def check(cmd, multiline):
    # app_log.info("Checking %s" % cmd)
    if cmd.lower() == 'sg' and multiline:
      return True
    else:
      return False


def run(lines):
    global app_log, command_regex

    app_log = setup_logging("signal-send")

    command_regex = re.compile('^(?P<command>[a-zA-Z ]+)$')

    app_log.info("Forwarding Signal Message")
    toL = lines[1]
    m = re.match("To:? (.*)$", toL)
    if m:
      to = m.group(1).replace(' ', '')
      app_log.info("Matched To: %s" % to)
      msg = '\n'.join(lines[2:])
      app_log.info("Sending Signal msg:\n%s" % msg)
      try:
          args = [SIGNAL_CLI_PATH, '-u', SIGNAL_NUMBER, 'send', '-m', msg, to]
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
      ret = "Couldn't match To: %s" % toL
      app_log.info(ret)
    return ret

command_list.append({
    'name' : 'SG-Forwarder',
    'check': check,
    'run': run
})
