#!/usr/bin/python3
import os, argparse, re, subprocess, time, traceback
import importlib
from smsgateway import sink_sms
from smsgateway.config import *
from smsgateway.sources.utils import *

app_log = setup_logging("sms")

src_path = os.path.dirname(os.path.abspath(__file__))

command_list = []

def handleCommand(mods, text):
  lines = text.strip().split('\n')
  cmd = lines[0].lower().strip()
  ret = "Unknown Command:\n%s" % text
  to = CONTROL_PHONES[0]
  app_log.info("Message has %s lines" % len(lines))
  #if len(lines) == 1:
  app_log.info("Commands: %s" % str(mods))
  multiline = len(lines) > 1
  for c in mods:
      if c.check(cmd, multiline):
          print(f"Mod {c} matched :)")
          try:
              ret = c.run(lines)
          except Exception as e:
              trace = traceback.format_exc()
              msg = "Run failed for command %s:\n%s\n%s" % (cmd, e, trace)
              app_log.error(msg)
              sink_sms.send_notif(msg)
          break
  # elif len(lines) > 2:
  #   if cmd == "SMS":
  #     print("Forwarding SMS")
  #     toL = lines[1]
  #     m = re.match("To: ([0-9 +]+)", toL)
  #     if m:
  #       to = m.group(1).replace(' ', '')
  #       print("Matched To: %s" % to)
  #       ret = '\n'.join(lines[2:])
  #     else:
  #       print("Couldn't match To: %s" % to)
  if ret:
    sink_sms.send_to(to, ret)

def readSMS(filename, received=True):
    direction = "From" if received else "To"
    address = None
    textStarted = False
    decodeUCS2 = False
    text = ''
    decoded_lines = []
    data = {}
    with open(filename, 'rb') as f:
      app_log.info("Opened received SMS")
      lines = f.readlines()
      for line in lines:
          if textStarted == True and decodeUCS2:
            line = line.decode("utf-16-be")
          else:
            line = line.decode("iso8859-15")
          line = line.rstrip()
          decoded_lines.append(line)
          if textStarted == True:
              text += "%s\n" % line
          else:
              m = re.match(f"{direction}: ([0-9]+)", line)
              m2 = re.match(f"{direction}: ([A-Za-z0-9]+)", line)
              mAlpha = re.match("Alphabet: ([A-Z0-9]+)", line)
              if mAlpha:
                  alpha = mAlpha.group(1)
                  if alpha == "UCS2":
                      decodeUCS2 = True
                  elif alpha == "ISO":
                      decodeUCS2 = False
              elif m or m2:
                  if m:
                    address = "+%s" % m.group(1)
                  else:
                    address = "%s" % m2.group(1)
                    app_log.info("Number is not numeric!")
                  app_log.info(f"{direction}: %s" % address)
              elif line == "":
                  textStarted = True
              else:
                  m = re.match(f"([^:]+): (.+)", line)
                  if m:
                      data[m.group(1)] = m.group(2)
    data.update({
      'address': address,
      'text': text,
      'lines': decoded_lines
    })
    return data

def handleSMS(mods, f):
    app_log.info("Received SMS, file: %s" % f)
    data = readSMS(f, received=True)
    # From = None
    # textStarted = False
    # decodeUCS2 = False
    # text = ''
    # with open(f, 'rb') as f:
    #   app_log.info("Opened received SMS")
    #   lines = f.readlines()
    #   for line in lines:
    #     if textStarted == True and decodeUCS2:
    #       line = line.decode("utf-16-be")
    #     else:
    #       line = line.decode("iso8859-15")
    #
    #     line = line.rstrip()
    #     m = re.match("From: ([0-9]+)", line)
    #     m2 = re.match("From: ([A-Za-z0-9]+)", line)
    #     mAlpha = re.match("Alphabet: ([A-Z0-9]+)", line)
    #     if textStarted == True:
    #         text += "%s\n" % line
    #     elif m or m2:
    #         if m:
    #           From = "+%s" % m.group(1)
    #         else:
    #           From = "%s" % m2.group(1)
    #           app_log.info("Number is not numeric!")
    #         app_log.info("From: %s" % From)
    #     elif mAlpha:
    #         alpha = mAlpha.group(1)
    #         if alpha == "UCS2":
    #             decodeUCS2 = True
    #         elif alpha == "ISO":
    #             decodeUCS2 = False
    #     elif line == "":
    #         textStarted = True
    From = data['address']
    text = data['text']
    if From and text:
      if From in ['+%s' % num for num in CONTROL_PHONES]:
        handleCommand(mods, text)
      else: # SMS from someone else
        app_log.info("Sending SMS")
        sink_sms.send("SMS", text, From)
    else:
      app_log.error("Couldn't parse incoming sms!")

def resendSMS(f):
  # textStarted = False
  # To = None
  # textStarted = None
  # wholeText = ''
  # text = ''
  # with open(f, 'r', encoding="8859") as f:
  #   app_log.info("Opened failed SMS")
  #   for line in f:
  #     line = line.rstrip()
  #     wholeText += line
  #     if textStarted == True:
  #       text += "%s\n" % line
  #     else:
  #       m = re.match("To: ([0-9]+)", line)
  #       m_fail = re.match("Fail_reason: (.*)", line)
  #       if m:
  #         To = "+%s" % m.group(1)
  #       elif m_fail:
  #         fail_reason = m_fail.group(1)
  #         app_log.warning("Fail reason: %s" % fail_reason)
  #       elif line == "":
  #         textStarted = True

    data = readSMS(f, received=False)
    To = data['address']
    text = data['text']
    fail_reason = "N/A"
    if 'Fail_reason' in data:
      fail_reason = data['Fail_reason']
    if To and text:
      if To in CONTROL_PHONES:
        app_log.warning("Resending SMS to CONTROL_PHONE")
        new_text = "RESEND: %s\n%s" % (fail_reason, text)
        sink_sms.send_notif(new_text)
      else:
        app_log.warning("Resending SMS to %s" % To)
        sink_sms.send_to(To, text)
        new_text = "RESEND: %s\n%s" % (fail_reason, text)
        sink_sms.send_notif(new_text)
    else:
      new_text = "Invalid failed SMS:\n%s" % '\n'.join(data['lines'])
      app_log.error(new_text)
      sink_sms.send_notif(new_text)

def main(mods):
    app_log.info(src_path)
    parser = argparse.ArgumentParser()
    parser.add_argument("event")
    parser.add_argument("file")
    args = parser.parse_args()

    if not args.event:
      app_log.error("Unknown command, use -h for help")
    else:
      if args.event == "RECEIVED":
        handleSMS(mods, args.file)
      elif args.event == 'FAILED':
        if args.file:
          app_log.warning("SMS failed. Process:")
          app_log.warning("- Stopping smstools.. ")
          (result, out) = run_cmd([SUDO_PATH, SYSTEMCTL_PATH, 'stop', 'smstools'])
          if result == 0:
            app_log.info("Success!")
          else:
            app_log.error("Error:\n%s" % out)

          app_log.info("- Resending: %s" % args.file)
          resendSMS(args.file)
          app_log.warning("- Reboot!")
          for handler in app_log.handlers:
            handler.flush()
          app_log.warning('')
          (res, out) = run_cmd([SUDO_PATH, REBOOT_PATH], "Reboot")
          if res != 0:
            app_log.error("Reboot failed: %s" % out)
        else:
          app_log.error("Got FAILED event, but no file!?")
      else:
        app_log.error("Event is %s, expected RECEIVED" % args.event)

if __name__ == '__main__':
    try:
      mods = []
      mod_specs = []

      for file in os.listdir(os.path.join(src_path, 'commands')):
            ext_file = os.path.splitext(file)

            if ext_file[1] == '.py' and not ext_file[0] == '__init__':
                mod_name = 'smsgateway.sources.commands.' + ext_file[0]
                spec = importlib.util.find_spec(mod_name)
                if spec not in mod_specs:
                  mod_specs.append(spec)
                  app_log.info("Importing %s" % ext_file[0])
                  m = importlib.import_module(mod_name)
                  mods.append(m)
                  # mod_names.add(mod_name)
                  # print(mod_names)

      main(mods)
    except Exception as e:
      app_log.error("Execution failed: %s" % e, exc_info=True)
