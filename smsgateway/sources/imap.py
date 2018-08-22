import email, time, argparse
from smsgateway import sink_sms
from smsgateway.sources.utils import *
from smsgateway.config import *

from imapclient import IMAPClient
from email.header import decode_header, make_header
from email.utils import parseaddr
from bs4 import BeautifulSoup

IDENTIFIER = "EM"

app_log = None

def parse_part(part):
    payload = None
    if part.get_content_maintype() == 'text':
        type = part.get_content_subtype()
        charset = 'UTF-8'
        charsets = part.get_charsets()
        if len(charsets) > 0:
            charset = charsets[0]
        app_log.debug(f"Decoding payload with charset {charset}")
        payload = part.get_payload(decode=True).decode(charset)
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
        body = parse_part(msg)
    if body and attachment:
        body += "\n\n----\n\n%s" % attachment
    elif not body:
        body = "No body!"
    items = {'Body': body}
    for name in ['Subject', 'From']:
        items[name] = make_header(decode_header(msg[name]))
    to_addr = parseaddr(msg['To'])
    to = to_addr[len(to_addr) - 1]
    if not to:
        to = make_header(decode_header(msg['To']))
    items['To'] = to

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

def forward_messages(messages):
    for msg in messages:
        body = msg['Body']
        del msg['Body']
        app_log.debug("Forwarding message: %s" % str(msg))
        sink_sms.send_dict(IDENTIFIER, body, msg)

def login(name):
    account = EMAIL_ACCOUNTS[name]
    server = IMAPClient(account['Host'])
    server.login(account['User'], account['Password'])
    inbox = server.select_folder('INBOX', readonly=True)
    app_log.debug("Inbox: %s" % inbox)
    return server

def wait_idle(server, account):
    last_exists = 0
    unseen = server.folder_status('INBOX', what=b'UNSEEN')[b'UNSEEN']
    app_log.info("Waiting for IDLE response..")
    server.idle()
    loop_start = time.time()
    while True:
        # noop = server.noop()
        # app_log.debug("Server returned %s" % noop)
        app_log.debug("Checking IDLE")
        start = time.time()
        responses = server.idle_check(timeout=10)
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
              try:
                  server.idle_done()
              except:
                  pass
              messages = fetch_messages(server, num)
              forward_messages(messages)
              server.idle()
        elif diff < 5:
            app_log.warning(f"IDLE check took only {diff} seconds!\nNeed to reconnect..")
            server = login(account)
        elif time.time() - loop_start >= 60:
            # Still connected but IDLE empty -> check if really no change
            app_log.debug("Checking if unseen messages increased..")
            try:
                server.idle_done()
            except:
                pass
            new_unseen = server.folder_status('INBOX', what=b'UNSEEN')[b'UNSEEN']
            diff = new_unseen - unseen
            if diff > 0:
              app_log.info(f"Found {diff} unseen messages!")
              messages = fetch_messages(server, diff)
              forward_messages(messages)
              unseen = new_unseen
            else:
              app_log.debug(f"No new unseen messages: {new_unseen} = {unseen}")
            server.idle()

        if time.time() - loop_start > 60*15:
            app_log.info("IDLE timeout elapsed, re-establishing connection..")
            try:
                server.idle_done()
            except:
                pass
            try:
                server.logout()
            except:
                pass
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
