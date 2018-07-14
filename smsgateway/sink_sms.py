import datetime, os
from smsgateway.config import *
from smsgateway.sources.utils import *

def send_dict(type, text, headers):
    send_to(CONTROL_PHONES[0], format_sms(type, text, headers))
def send(type, text, _from, phone=None, group=None):
    lines = [
        type,
        f"From: {_from}"
    ]
    if group:
        lines += [f"Group: {group}"]
    if phone:
        lines += [f"Phone: {phone}"]
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
    print("Sending SMS:\n%s" % text)
    header = '\n'.join([f"To: {to}", "Alphabet: UCS-2", "", ""])
    d = datetime.datetime.now().strftime("%y-%m-%d_%H-%M-%S.%f")[:-3]
    p = os.path.join(SMS_DIR, d)
    print("Writing sms to %s" % p)
    with open(p, 'wb') as f:
        f.write(header.encode("UTF-8"))
        f.write(text.encode("utf-16-be"))
        f.flush()
