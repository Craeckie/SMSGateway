#!/usr/bin/python
import subprocess, datetime, os, sys, re, json, textwrap
from smsgateway import sink_sms
from smsgateway.sources.utils import *
from smsgateway.config import *

import logging
from logging.handlers import RotatingFileHandler
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
logFile = os.path.join(LOG_DIR, 'telegram.log')
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.DEBUG)
app_log = logging.getLogger('root')
app_log.setLevel(logging.DEBUG)
app_log.addHandler(my_handler)

IDENTIFIER = "TG"

def listen():
    print("Starting telegram..")
    proc = subprocess.Popen([TELEGRAM_CLI_PATH, '-RW', '--json', '--disable-colors', '-k', TELEGRAM_KEY_PATH], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stdout.buffer)

    while proc.poll() == None:
        line = proc.stdout.readline().decode('UTF-8')
        app_log.debug(line)
        #proc.stdin.write(bytes('\n', 'UTF-8'))
        res = parse_message(line)
        if res:
          (m, f, to, from_id) = res
          app_log.info("From: %s\n" % f)

          if from_id != TG_USER_ID:
            app_log.info("Forwarding message:\n%s" % m)
            sink_sms.send(IDENTIFIER, f, m)
          else:
            app_log.info("Forwarding message from myself:\n%s" % m)
            sink_sms.send_from_me(IDENTIFIER, to, m)

def parse_message(line):
  if line != '':
      line_cleaned = line.strip()
      m = re.match("^>?[^{]*(\{.*\})$", line_cleaned)
      if m:
          line_cleaned = m.group(1)
          app_log.debug(line_cleaned)
          j = json.loads(line_cleaned)
          event = j['event']
          #print("Event: %s" % event)
          if event == 'message':
            try:
              f = j['from']['print_name']
              m = ''
              if 'reply_id' in j and j['reply_id']:
                app_log.info("Adding reply_to for id %s" % j['reply_id'])
                command = "get_message %s" % j['reply_id']
                try:
                  (success, res) = run_cmd([TELEGRAM_CLI_PATH, "-D", "--json", "-k", TELEGRAM_KEY_PATH, "--profile", "profile_send", "-RW", "-e", command], timeout=30)
                  if success:
                    app_log.debug("Successful get_message command")
                    for l in res.split('\n'):
                      app_log.debug("Line: %s" % l)
                      try:
                        res2 = parse_message(l)
                        if res2:
                          (m2, f2, to2, from_id) = res2
                          app_log.info("Found reply:\n%s" % m)
                          m = "Reply to %s:\n%s\n\n" % (f2, textwrap.indent(m2, '> '))
                          break
                        else:
                          app_log.warning("Reply_to: parse_message failed")
                      except Exception as e:
                        app_log.warning("Reply_to: parse_message failed:\n%s" % e)
                        pass
                  else:
                    app_log.warning("Reply_to: get_message failed:\n%s" % res)
                except Exception as e:
                  app_log.warning("Reply_to: get_message failed:\n%s" % e)

              if 'media' in j:
                media_type = j['media']['type']
                m += "Media: %s" % media_type.capitalize()
                #TODO: not working?
                if media_type == 'geo' and 'latitude' in j['media'] and 'longitude' in j['media']:
                  m += "\nhttps://osmand.net/go?lat=%s&lon=%s&z=15" %(j['media']['latitude'], j['media']['longitude'])
                elif media_type == 'contact' and ('phone' in j['media'] or 'first_name' in j['media']):
                  m += "\n"
                  m += ' '.join([x for x in j['media'][field] for field in ['first_name', 'last_name', 'phone']])
                if 'caption' in j['media'] and j['media']['caption']:
                  m += "\n%s" % j['media']['caption']
                if 'text' in j:
                  m += "\n%s" % j['text']
              elif 'text' in j:
                m += j['text']

              m = replaceEmoticons(m)
              peer_type = j['to']['peer_type']
              if peer_type == 'chat':
                # Group message
                to = j['to']['print_name'] if 'print_name' in j['to'] else j['to']['title']
                f += "@%s" % to
              elif peer_type == 'user':
                if 'username' in j['to']:
                  to_id = j['to']['username']
                to = j['to']['print_name']
              else:
                app_log.warning("Unknown peer_type: %s" % peer_type)
              from_id = j['from']['peer_id']
              return (m, f, to, from_id)
            except KeyError:
              app_log.error("KeyError in message \"%s\"" % line_cleaned)

listen()
