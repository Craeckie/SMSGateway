import datetime, os
from smsgateway.config import *

def send_dict(type, text, headers):
    msg = f"{type}\n"
    msg += '\n'.join([f"{k[0].upper + k[1:]}: {v}" for k,v in headers.items() if len(k) > 1])
    msg += f"\n\n{text}"
    send_to(CONTROL_PHONES[0], msg)
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
