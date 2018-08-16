from smsgateway import sink_sms
from smsgateway.sources.utils import *
from smsgateway.config import *

from imapclient import IMAPClient
import email
from email.header import decode_header, make_header
from bs4 import BeautifulSoup

app_log = setup_logging("email")

IDENTIFIER = "EM"

def parse_fetch(fetch):
    msg = email.message_from_bytes(fetch)
    body = None
    if msg.is_multipart():
        for part in msg.get_payload():
            if part.get_content_maintype() == 'text':
                body = part.get_payload(decode=True).decode('UTF-8')
    else:
        body = msg.get_payload(decode=True).decode('UTF-8')
        type = msg.get_content_type()
        if type == 'text/html':
            # Extract the actual text content
            b = BeautifulSoup(body, 'html.parser')
            for s in b(["script", "style"]):
                s.decompose()
            text = b.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            body = text
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

def wait_idle(server):
    app_log.info("Waiting for IDLE response..")
    server.idle()
    last_exists = 0
    while True:
      app_log.debug("Checking IDLE")
      responses = server.idle_check(timeout=30)
      app_log.debug("Server sent: %s" % responses if responses else "nothing")
      if responses:
          num = 0
          for (n, type) in responses:
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

    server.idle_done()

def main():
    app_log.info("Logging in..")
    server = IMAPClient(EMAIL_HOST)
    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
    server.select_folder('INBOX')

    wait_idle(server)

    server.logout()

if __name__ == '__main__':
    main()
