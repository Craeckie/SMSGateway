import re, json
from smsgateway.sources.sms import command_list
from smsgateway.config import *
from smsgateway.sources.utils import *
from smsgateway import sink_sms
from telethon import TelegramClient, utils

app_log = setup_logging("telegram-send")

IDENTIFIER = "TG"

command_regex = re.compile('^(?P<command>[a-zA-Z ]+)$')

api_id = 242101
api_hash = "80cbc97ce425aae38c1e0291ef2ab2a4"

session_path = os.path.join(CONFIG_DIR, 'telegram-send')

def check(cmd, multiline):
    # print("Checking %s" % cmd)
    if cmd.lower() == IDENTIFIER.lower() and multiline:
      return True
    else:
      return False


def run(lines):
    print("Forwarding Telegram Message")
    messageStarted = False
    to_matched = None
    message = ""

    for line in lines[1:]: # skip IDENTIFIER
        if messageStarted:
            message += f"\n{line}"
        elif not line.strip(): # empty line
            messageStarted = True
            message += line
        else:
            mTo = re.match("To: (.*)$", line)
            if mTo:
                to_matched = mTo.group(1).strip()
            else:
                app_log.warning(f"Unkown header: {line}!")

    if to_matched and message:
      print("Starting client..")
      client = TelegramClient(session_path, api_id, api_hash)
      try:
          client.start()
      except Exception as e:
          ret = "Could not connect! Run python3 -m smsgateway.sources.commands.send_telegram_new to authorize!\nError: %s" % e
          app_log.error(ret)
          return ret

      to = None
      for x in client.iter_dialogs():
          name = utils.get_display_name(x.entity)
          if name == to_matched:
            to = x.entity.id
            print("Found it via display_name: %s" % x.entity.stringify())
            break
      if not to:
          print(f"Couldn't find {to}! Trying directly..")
          to = name = to_matched

      print("Sending Telegram msg:\n%s" % message)
      # arg = "msg %s %s" % (to, msg)
      # print("Calling Telegram with %s" % arg)
      import getpass
      print("I am: %s" % getpass.getuser())

      client.send_message(to, message)
      client.disconnect()
      ret = '\n'.join([
        IDENTIFIER,
        f"To: {name}",
        "",
        message
      ])
      # try:
      #     #res = subprocess.check_output(["sudo", "-Hu", "pi", "/home/pi/tg/bin/telegram-cli", "-D", "--json", "-RW", "-e", arg], stderr=subprocess.STDOUT).decode('UTF-8').strip()
      #     res = subprocess.check_output([TELEGRAM_CLI_PATH, "-D", "--json", "-k", TELEGRAM_KEY_PATH, "--profile", "profile_send", "-RW", "-e", arg], stderr=subprocess.STDOUT, timeout=300).decode('UTF-8').strip()
      # except subprocess.TimeoutExpired as e:
      #     return "Timeout when sending TG to %s: %s" % (to, e)
      # except subprocess.CalledProcessError as e:
      #     return "Failed to send TG to %s: %s" % (to, e.output)
      # lines = res.split('\n')
      # print("Got %s" % lines)
      # if len(lines) >= 1:
      #   for l in lines:
      #       try:
      #           j = json.loads(l.strip())
      #           if j and j['result'] == 'SUCCESS':
      #             ret = f'TG\nTo: {to}\n{msg}'
      #             break
      #           elif j:
      #             try:
      #                 ret = f"Failed to send TG to {to}:\n{j['error']}"
      #                 break
      #             except Exception as e:
      #                 ret = "Failed to send TG to %s!" % to
      #           else:
      #             ret = "Failed to send TG to %s!" % to
      #       except ValueError:
      #           ret = "Failed to send TG to %s!" % to
      # else:
      #   ret = "Failed to send TG to %s!" % to
    else:
      ret = "Couldn't match To: %s" % to_matched
      print(ret)
    return ret

if __name__ == '__main__':
    client = TelegramClient(session_path, api_id, api_hash)
    if not client.start():
        app_log.error("Could not connect! Run python3 -m smsgateway.source.telegram to authorize!")
        sys.exit(1)

command_list.append({
    'name' : 'TG-Forwarder-new',
    'check': check,
    'run': run
})
