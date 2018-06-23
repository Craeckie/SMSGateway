#!/usr/bin/python
import subprocess, datetime, os, sys, re, json
from smsgateway import sink_sms
from smsgateway.config import *
from smsgateway.sources.utils import *

app_log = setup_logging("telegram")

IDENTIFIER = "SG"

def listen():
    print("Starting signal-cli..")
    #TODO: remove -t?
    proc = subprocess.Popen([SIGNAL_CLI_PATH, '-u', SIGNAL_NUMBER, 'receive', '--json', '-t', '300'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stdout.buffer)

    while proc.poll() == None:
        line = proc.stdout.readline().decode('UTF-8')
        app_log.debug(line)
        #proc.stdin.write(bytes('\n', 'UTF-8'))
        if line != '':
            try:
                j = json.loads(line)
                envelope = j['envelope']
                source = envelope['source']
                dataMsg = envelope['dataMessage']
                syncMsg = envelope['syncMessage']
                if dataMsg:
                    msg = dataMsg['message']
                    app_log.info("From: %s\n\n%s\n" % (source, msg))
                    sink_sms.send(IDENTIFIER, msg, source)
                elif syncMsg and source == SIGNAL_NUMBER:
                    msg = syncMsg['message']
                    app_log.info("From: %s\n\n%s\n" % (source, msg))
                    app_log.info("Message from myself: %s" % line)
                    continue
            except KeyError:
              app_log.warning("KeyError in message \"%s\"" % line_cleaned)
            # with open ('/var/log/signal.log', 'a') as f:
            #   f.write("%s\n" % line)
            app_log.info("Unknown message: %s" % line)

listen()

# {
#   "envelope": {
#     "source": "+49123123123",
#     "sourceDevice": 2,
#     "relay": null,
#     "timestamp": 1499249864225,
#     "isReceipt": false,
#     "dataMessage": {
#       "timestamp": 1499249864225,
#       "message": "abc",
#       "expiresInSeconds": 0,
#       "attachments": [],
#       "groupInfo": null
#     },
#     "syncMessage": null,
#     "callMessage": null
#   }
# }
