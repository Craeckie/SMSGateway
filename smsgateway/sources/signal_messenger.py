#!/usr/bin/python
import subprocess, datetime, os, sys, re, json
from smsgateway import sink_sms
from smsgateway.config import *
from smsgateway.sources import utils

app_log = utils.setup_logging("signal")

IDENTIFIER = "SG"

def listen(groups={}):
    app_log.info("Starting signal-cli..")
    proc = subprocess.Popen([utils.SIGNAL_CLI_PATH, '-u', utils.SIGNAL_NUMBER, 'receive', '--json', '-t', str(12 * 3600)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stdout.buffer)

    while proc.poll() == None:
        line = proc.stdout.readline().decode('UTF-8')
        app_log.debug(line)
        #proc.stdin.write(bytes('\n', 'UTF-8'))
        if line != '':
            try:
                j = json.loads(line)
                envelope = j['envelope']
                source = envelope['source']
                chat_info = {
                    'ID': envelope['timestamp'],
                }

                dataMsg = envelope['dataMessage']
                syncMsg = envelope['syncMessage']
                info = dataMsg if dataMsg else syncMsg if syncMsg else None
                if info:
                    if 'sentMessage' in info and info['sentMessage']:
                        info = info['sentMessage']
                    if 'message' in info:
                        msg = info['message']
                        if 'groupInfo' in info and info['groupInfo']:
                            groupInfo = info['groupInfo']
                            groupID = groupInfo['groupId']
                            chat_info.update({
                                'type': 'Group',
                                'groupID': groupID,
                            })
                            if groupInfo['type'] == 'UPDATE' and 'name' in groupInfo and groupInfo['name']: # new/changed group
                                if not msg:
                                    if groupID in groups:
                                        msg = 'Group was changed!'
                                    else:
                                        msg = 'Group was created!'
                                    if 'members' in groupInfo:
                                        msg += '\nMembers: ' + ', '.join(groupInfo['members'])
                                groups[groupID] = groupInfo['name']
                            if groupID in groups:
                                chat_info['to'] = groups[groupID]
                            else:
                                app_log.warning(f'Group with ID {groupID} not in group list!')
                            if source != utils.SIGNAL_NUMBER:
                                chat_info.update({
                                    'from': source,
                                    'phone': source,
                                })
                        elif source == utils.SIGNAL_NUMBER and 'destination' in info:  # from me
                            chat_info.update({
                                'to': info['destination'],
                                'phone': info['destination'],
                            })
                        else:
                            chat_info.update({
                                'from': source,
                                'phone': source,
                            })
                        if msg and ('from' in chat_info or 'to' in chat_info):
                            sink_sms.send_dict(IDENTIFIER, msg, chat_info)
                else:
                    app_log.info("Unknown message: %s" % line)
            except KeyError:
                app_log.warning("KeyError in message \"%s\"" % line, exc_info=True)
            # with open ('/var/log/signal.log', 'a') as f:
            #   f.write("%s\n" % line)


def getGroups():
    app_log.info("Getting groups from signal-cli..")
    groups = {}
    try:
        output = subprocess.check_output([utils.SIGNAL_CLI_PATH, '-u', utils.SIGNAL_NUMBER, 'listGroups'], stderr=subprocess.STDOUT, text=True, timeout=300)
        for line in output.splitlines():
            m = re.match('Id: (?P<id>[^ ]+) +Name: (?P<name>[^ ]+) +Active: (?P<active>[^ ]+)$', line)
            if m:
                groupID = m.group('id')
                groupName = m.group('name')
                groups[groupID] = groupName
                app_log.info(f'{groupID}: {groupName}')
            else:
                app_log.warning(f'Couldn\' group definition:\n{line}')
    except subprocess.CalledProcessError  as e:
        app_log.warning(f'Couldn\'t get groups from signal :(\nError:\n{e.output}')
    return groups


groups = getGroups()
listen(groups)

# {
#   "envelope": {
#     "source": "+491743624125",
#     "sourceDevice": 1,
#     "relay": null,
#     "timestamp": 1572988173059,
#     "isReceipt": false,
#     "dataMessage": {
#       "timestamp": 1572988173059,
#       "message": "ugh",
#       "expiresInSeconds": 0,
#       "attachments": [],
#       "groupInfo": null
#     },
#     "syncMessage": null,
#     "callMessage": null,
#     "receiptMessage": null
#   }
# }

# {
#   "envelope": {
#     "source": "+491743624125",
#     "sourceDevice": 1,
#     "relay": null,
#     "timestamp": 1572987164644,
#     "isReceipt": false,
#     "dataMessage": null,
#     "syncMessage": {
#       "sentMessage": {
#         "timestamp": 1572987164644,
#         "message": "test",
#         "expiresInSeconds": 604800,
#         "attachments": [],
#         "groupInfo": null,
#         "destination": "+4915756542328"
#       },
#       "blockedNumbers": null,
#       "readMessages": null,
#       "type": null
#     },
#     "callMessage": null,
#     "receiptMessage": null
#   }
# }

# Group created
# {
#   "envelope": {
#     "source": "+491743624125",
#     "sourceDevice": 1,
#     "relay": null,
#     "timestamp": 1572988370215,
#     "isReceipt": false,
#     "dataMessage": {
#       "timestamp": 1572988370215,
#       "message": "",
#       "expiresInSeconds": 0,
#       "attachments": [],
#       "groupInfo": {
#         "groupId": "eEQ4OfkXuF4/gPQKlaDX8A==",
#         "members": [
#           "+491743624125",
#           "+4915771087176"
#         ],
#         "name": "aha",
#         "type": "UPDATE"
#       }
#     },
#     "syncMessage": null,
#     "callMessage": null,
#     "receiptMessage": null
#   }
# }

# Group message
# {
#   "envelope": {
#     "source": "+491743624125",
#     "sourceDevice": 1,
#     "relay": null,
#     "timestamp": 1572988387668,
#     "isReceipt": false,
#     "dataMessage": {
#       "timestamp": 1572988387668,
#       "message": "lol",
#       "expiresInSeconds": 0,
#       "attachments": [],
#       "groupInfo": {
#         "groupId": "eEQ4OfkXuF4/gPQKlaDX8A==",
#         "members": null,
#         "name": null,
#         "type": "DELIVER"
#       }
#     },
#     "syncMessage": null,
#     "callMessage": null,
#     "receiptMessage": null
#   }
# }
