#!/usr/bin/python
import subprocess, datetime, os, sys, re, json
from time import sleep

from smsgateway import sink_sms
from smsgateway.config import *
from smsgateway.sources.utils import *
from .signal_utils import connect


def init():
    global IDENTIFIER, app_log, session_path
    app_log = setup_logging("signal")

    IDENTIFIER = "SG"

    session_path = os.path.join(CONFIG_DIR, 'signal')


def listen():
    print("Starting signal-cli..")
    # TODO: remove -t?
    proc = subprocess.Popen([
            SIGNAL_CLI_PATH,
            '--config', session_path,
            '-u', SIGNAL_NUMBER,
            'receive',
            '--json',
            '-t', '-1',
        ],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while proc.poll() is None:
        line = proc.stdout.readline().decode('UTF-8')
        app_log.debug(line)
        # proc.stdin.write(bytes('\n', 'UTF-8'))
        if line != '':
            try:
                j = json.loads(line)
                envelope = j['envelope']
                source = envelope['source']
                dataMsg = envelope['dataMessage']
                syncMsg = envelope['syncMessage']
                info = {
                    'date': envelope['timestamp']
                }
                if dataMsg:
                    msg = dataMsg['message']
                    info['from'] = source
                    app_log.info(f"From: {source}\n\n{msg}\n")
                elif syncMsg and source == SIGNAL_NUMBER and 'sentMessage' in syncMsg:
                    sentMsg = syncMsg['sentMessage']
                    info['to'] = source
                    if sentMsg and 'message' in sentMsg and sentMsg['message']:
                        msg = sentMsg['message']
                        app_log.info(f"Message from myself:\n{line}")
                        app_log.info("From: %s\n\n%s\n" % (source, msg))
                    else:
                        app_log.warning(f"Sent Message contains no message:\n{line}")
                        continue
                else:
                    app_log.info(f"Has no dataMessage or syncMessage:\n{line})")
                    continue
                sink_sms.send_dict(IDENTIFIER, msg, info)
            except KeyError:
                app_log.warning(f"KeyError in message:\n{line}", exc_info=True)
            # with open ('/var/log/signal.log', 'a') as f:
            #   f.write("%s\n" % line)
            app_log.info(f"Couldn't parse message:\n{line}")


if __name__ == '__main__':
    init()
    if connect(app_log, session_path):
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
