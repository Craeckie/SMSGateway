import datetime, os
import smsgateway.config as conf
from smsgateway.sources.utils import *
from cryptography.fernet import Fernet

def send_dict(type, text, headers):
    send_to(conf.CONTROL_PHONES[0], format_sms(type, text, headers))
def send(type, text, _from, phone=None, group=None):
    lines = [
        type,
        f"From: {_from}"
    ]
    if group:
        lines += [f"Group: {group}"]
    if phone:
        lines += [f"Phone: {phone}"]
    if text:
        lines += [
            "",
            text
        ]
    send_to(conf.CONTROL_PHONES[0], '\n'.join(lines))

def send_from_me(type, text, to):
    lines = [
        type,
        f"To: {to}",
        "",
        text
    ]
    send_to(conf.CONTROL_PHONES[0], '\n'.join(lines))

def send_notif(text):
    send_to(conf.CONTROL_PHONES[0], text)

def send_to(to, text):
    print("Sending SMS:\n%s" % text)

    d = datetime.datetime.now().strftime("%y-%m-%d_%H-%M-%S.%f")[:-3]
    p = os.path.join(SMS_DIR, d)
    if conf.KEY:
        alphabet = "ISO"
        f = Fernet(conf.KEY)
        encrypted = f.encrypt(text.encode("utf-8"))
        msg = "%8%" + encrypted.decode("utf-8")
    else:
        alphabet = "UCS-2"
        msg = text
    header = '\n'.join([f"To: {to}", f"Alphabet: {alphabet}", "", ""])
    print("Writing sms to %s" % p)
    with open(p, 'wb') as f:
        f.write(header.encode("UTF-8"))
        f.write(msg.encode("UTF-8"))
        f.flush()
