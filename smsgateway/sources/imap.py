import email, time, argparse
from smsgateway import sink_sms
from smsgateway.sources.utils import *
from smsgateway.config import *

from imapclient import IMAPClient
from email.header import decode_header, make_header
from bs4 import BeautifulSoup

IDENTIFIER = "EM"

app_log = None

def parse_part(part):
    payload = None
    if part.get_content_maintype() == 'text':
        type = part.get_content_subtype()
        payload = part.get_payload(decode=True).decode('UTF-8')
        if type == 'html':
            b = BeautifulSoup(payload, 'html.parser')
            for s in b(["script", "style"]):
                s.decompose()
            text = b.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            payload = text
    return payload

def parse_fetch(fetch):
    msg = email.message_from_bytes(fetch)
    body = None
    attachment = None
    if msg.is_multipart():
        for part in msg.get_payload():
            payload = parse_part(part)
            if payload:
              if part.get_content_disposition() == 'attachment':
                  name = part.get_filename()
                  attachment = "Attachment: %s\n\n%s" % (name, payload)
              else:
                  body = payload
    else:
        body = parse_part(part)
    if body and attachment:
        body += "\n\n----\n\n%s" % attachment
    elif not body:
        body = "No body!"
    items = {'Body': body}
    for name in ['Subject', 'From', 'To']:
        items[name] = make_header(decode_header(msg[name]))

    return items
def fetch_messages(server, num):
    app_log.info("Fetching %s messages" % num)
    msg_list = server.sort(sort_criteria='REVERSE DATE', charset='UTF-8')
    app_log.debug("Found %s messages" % len(msg_list))
    last_messages = msg_list[0:num]
    msg_fetches = server.fetch(last_messages, ['RFC822'])
    app_log.info("Fetched %s messages" % len(msg_fetches))
    messages = []
    for msg_id in last_messages:
        app_log.debug(msg_id)
        fetch = msg_fetches[msg_id]
        if b'RFC822' in fetch:
            msg = parse_fetch(fetch[b'RFC822'])
            messages.append(msg)
            for k, v in msg.items():
                app_log.debug("%s: %s" % (k, v))
        else:
            app_log.warning("No RFC822 in this fetch: %s" % fetch)
    return messages

def login(name):
    account = EMAIL_ACCOUNTS[name]
    server = IMAPClient(account['Host'])
    server.login(account['User'], account['Password'])
    inbox = server.select_folder('INBOX')
    app_log.debug("Inbox: %s" % inbox)
    return server

def wait_idle(server, account):
    app_log.info("Waiting for IDLE response..")
    server.idle()
    last_exists = 0
    loop_start = time.time()
    while True:
        # noop = server.noop()
        # app_log.debug("Server returned %s" % noop)
        app_log.debug("Checking IDLE")
        start = time.time()
        responses = server.idle_check(timeout=30)
        diff = time.time() - start
        app_log.debug("Server sent: %s" % responses if responses else "nothing")
        if responses:
            num = 0
            for resp in responses:
              if len(resp) >= 2:
                n = resp[0]
                type = resp[1]
                if type == b'EXISTS':
                  if n > last_exists:
                    num += 1
                  last_exists = n
            if num > 0:
              server.idle_done()
              messages = fetch_messages(server, num)
              for msg in messages:
                  body = msg['Body']
                  del msg['Body']
                  app_log.debug("Forwarding message: %s" % str(msg))
                  sink_sms.send_dict(IDENTIFIER, body, msg)
              server.idle()
        elif diff < 5:
            app_log.warning(f"IDLE check took only {diff} seconds!\nNeed to reconnect..")
            server = login()

        if time.time() - loop_start > 60*20:
            app_log.info("IDLE timeout elapsed, re-establishing connection..")
            server.idle_done()
            server.logout()
            server = login(account)
            loop_start = time.time()

    server.idle_done()

def main():
    global app_log
    parser = argparse.ArgumentParser()
    parser.add_argument("account", help="The account name from config.py")
    args = parser.parse_args()

    account = args.account

    app_log = setup_logging("email-%s" % account)


    app_log.info("Logging in..")
    server = login(account)

    wait_idle(server, account)

    server.logout()

if __name__ == '__main__':
    main()
