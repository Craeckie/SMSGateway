import datetime, os
from smsgateway.config import *

def send(type, text, _from, group=None):
    lines = [
        type,
        f"From: {_from}"
    ]
    if group:
        lines += [f"Group: {group}"]
    lines += [
        "",
        text
    ]
    send_to(CONTROL_PHONES[0], '\n'.join(lines))

def send_from_me(type, text, to):
    lines = [
        type,
        f"To: {to}",
        "",
        text
    ]
    send_to(CONTROL_PHONES[0], '\n'.join(lines))

def send_notif(text):
    send_to(CONTROL_PHONES[0], text)

def send_to(to, text):
    header = '\n'.join([f"To: {to}", "Alphabet: UCS-2", "", ""])
    d = datetime.datetime.now().strftime("%y-%m-%d_%H-%M-%S.%f")[:-3]
    p = os.path.join(SMS_DIR, d)
    print("Writing sms to %s" % p)
    with open(p, 'wb') as f:
        f.write(header.encode("UTF-8"))
        f.write(text.encode("utf-16-be"))
        f.flush()
