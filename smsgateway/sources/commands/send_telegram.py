import re, subprocess, json
from smsgateway.sources.sms import command_list
from smsgateway.config import *
from smsgateway import sink_sms

command_regex = re.compile('^(?P<command>[a-zA-Z ]+)$')

def check(cmd, multiline):
    print("Checking %s" % cmd)
    if cmd.lower() == 'tg' and multiline:
      return True
    else:
      return False


def run(lines):
    print("Forwarding Telegram Message")
    toL = lines[1]
    m = re.match("To: (.*)$", toL)
    if m:
      to = m.group(1).replace(' ', '')
      print("Matched To: %s" % to)
      msg = '\n'.join(lines[2:])
      print("Sending Telegram msg:\n%s" % msg)
      arg = "msg %s %s" % (to, msg)
      print("Calling Telegram with %s" % arg)
      import getpass
      print("I am: %s" % getpass.getuser())
      try:
          #res = subprocess.check_output(["sudo", "-Hu", "pi", "/home/pi/tg/bin/telegram-cli", "-D", "--json", "-RW", "-e", arg], stderr=subprocess.STDOUT).decode('UTF-8').strip()
          res = subprocess.check_output([TELEGRAM_CLI_PATH, "-D", "--json", "-k", TELEGRAM_KEY_PATH, "--profile", "profile_send", "-RW", "-e", arg], stderr=subprocess.STDOUT, timeout=300).decode('UTF-8').strip()
      except subprocess.TimeoutExpired as e:
          return "Timeout when sending TG to %s: %s" % (to, e)
      except subprocess.CalledProcessError as e:
          return "Failed to send TG to %s: %s" % (to, e.output)
      lines = res.split('\n')
      print("Got %s" % lines)
      if len(lines) >= 1:
        for l in lines:
            try:
                j = json.loads(l.strip())
                if j and j['result'] == 'SUCCESS':
                  ret = f'TG\nTo: {to}\n{msg}'
                  break
                elif j:
                  try:
                      ret = f"Failed to send TG to {to}:\n{j['error']}"
                      break
                  except Exception as e:
                      ret = "Failed to send TG to %s!" % to
                else:
                  ret = "Failed to send TG to %s!" % to
            except ValueError:
                ret = "Failed to send TG to %s!" % to
      else:
        ret = "Failed to send TG to %s!" % to
    else:
      ret = "Couldn't match To: %s" % toL
      print(ret)
    return ret

command_list.append({
    'name' : 'TG-Forwarder',
    'check': check,
    'run': run
})
