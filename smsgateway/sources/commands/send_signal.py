import re, subprocess, json, os
from smsgateway.sources.sms import command_list
from smsgateway.config import *
from smsgateway import sink_sms
from smsgateway.sources.utils import *
from ..signal_utils import connect
from .utils import parse_message

import logging
from logging.handlers import RotatingFileHandler

def init():
    global IDENTIFIER, app_log, command_regex, session_path
    IDENTIFIER = "SG"

    app_log = setup_logging("signal-send")

    command_regex = re.compile('^(?P<command>[a-zA-Z ]+)$')

    session_path = os.path.join(CONFIG_DIR, 'signal-send')

def check(cmd, multiline):
    init()
    # app_log.info("Checking %s" % cmd)
    if cmd.upper() == IDENTIFIER and multiline:
      return True
    else:
      return False


def run(lines):
    init()

    app_log.info("Forwarding Signal Message")
    # toL = lines[1]
    # m = re.match("To:? (.*)$", toL)
    # if m:
    #   to = m.group(1).replace(' ', '')
    #   app_log.info("Matched To: %s" % to)
    #   msg = '\n'.join(lines[2:])
    data = parse_message(app_log, lines)
    if data['success']:
      msg = data['message']
      to = data['to']
      app_log.info(f"Sending Signal msg:\n{msg}")
      try:
          args = [
              SIGNAL_CLI_PATH,
              '--config', session_path,
              '-u', SIGNAL_NUMBER,
              'send',
              '-m', msg,
              to,
          ]
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
      ret = data['error']
      app_log.info(ret)
    return ret

command_list.append({
    'name' : 'SG-Forwarder',
    'check': check,
    'run': run
})


if __name__ == '__main__':
    init()

    if not connect(app_log, session_path):
        print("Linking failed!")
    else:
        print("Successfully connected!")
