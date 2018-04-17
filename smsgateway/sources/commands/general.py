import re, subprocess, os
from smsgateway.sources.sms import command_list
from smsgateway.config import *
from smsgateway import sink_sms
from smsgateway.sources.utils import *

commands = ['stat', 'reboot', 'shutdown now', 'apt update', 'apt upgrade']
command_regex = re.compile(r'^(?P<command>[a-zA-Z ]+?)( full)?$')


def check(cmd, multiline):
    # print("Checking %s" % cmd)
    match = command_regex.match(cmd)
    if match:
      if match.group('command') in commands:
        # print("Command RE matches!")
        return True
    return False

def _stat_net(interface):
    try:
      out = subprocess.check_output(['ifconfig', interface])
    except subprocess.CalledProcessError as e:
      out = e.output
    if out:
      lines = out.decode('UTF-8').strip().split('\n')
      lines_n = [x.strip() for x in lines[:2]]
      lines_n += [lines[-1].strip()]
      return "%s\n" % '\n'.join(lines_n)
    else:
      return ""

from enum import Enum
class Status(Enum):
    DISABLED = 0
    ENABLED  = 1
    BOTH     = 2

def _stat_service(service, status=Status.BOTH):
    result = subprocess.call([SYSTEMCTL_PATH, 'is-enabled', service])
    is_enabled = 'disabled'
    if result == 0:
        if status == Status.DISABLED:
            return ''
        is_enabled = 'enabled'
    elif status == Status.ENABLED:
        return ''

    result = subprocess.call([SYSTEMCTL_PATH, 'is-active', service])
    is_active = 'Running'
    if result != 0:
        is_active = 'Stopped'
        result = subprocess.call([SYSTEMCTL_PATH, 'is-failed', service])
        if result != 0:
            is_active += " (failed)"
    return '%s: %s, %s\n' % (service, is_active, is_enabled)

from datetime import timedelta
def _stat_uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        uptime_string = str(timedelta(seconds = uptime_seconds))

    return uptime_string

def _sizeof_fmt(num, suffix='B'):
        for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
          if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
          num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

def _stat_df():
  statvfs = os.statvfs('/')

  df = _sizeof_fmt(statvfs.f_frsize * statvfs.f_bfree)
  return df

def status(full=False):
    ret = 'Status of SMSGateway:\n'
    ret += 'Uptime: %s\n' % _stat_uptime()
    ret += 'Free space: %s\n' % _stat_df()
    net_inf = NETWORK_INTERFACES_ALL if full else NETWORK_INTERFACES
    wifi_inf = WIFI_INTERFACES_ALL if full else WIFI_INTERFACES

    for interface in net_inf:
        ret += _stat_net(interface)

    for interface in wifi_inf:
        try:
          out = subprocess.check_output(['iwconfig', interface])
        except subprocess.CalledProcessError as e:
          out = e.output
        if out:
          lines = out.decode('UTF-8').strip().split('\n')
          ret += "%s\n" % lines[0].strip()
          if len(lines) > 5:
              ret += "%s\n" % lines[5].strip()

    ret += '\n'
    for s in SERVICES:
        ret += _stat_service(s, Status.ENABLED)
    if full:
        ret += "\nDisabled:\n"
        for s in SERVICES:
            ret += _stat_service(s, Status.DISABLED)

    return ret


def run(lines):
    cmd = lines[0]
    # print("Command RE matches!")
    m = command_regex.match(cmd)
    c = m.groupdict()['command']
    ret = None
    if c in commands:
      # print("Command: %s" % c)
      if c.startswith('stat'):
          ret = status(cmd == 'stat full')
      elif c == 'daemon-reload':
        (res, out) = run_cmd([SUDO_PATH, SYSTEMCTL_PATH], "daemon-reload")
        ret = "daemon-reload: "
        ret += "OK!" if res else "failed:"
        ret += "\n%s" % out
      elif c == 'shutdown now':
        print("Shutdown initiated..")
        print("Sending last SMS to %s" % CONTROL_PHONES[0])
        sink_sms.send_to(CONTROL_PHONES[0], "SMSGateway: Shutdown initiated.")
        ret = "SMSGateway: Shutdown initiated."
        subprocess.call([SUDO_PATH, SYSTEMCTL_PATH, 'poweroff'])
        print("Good bye!")
        return
      elif c == 'reboot':
        sink_sms.send_notif("SMSGateway: rebooting!")
        (res, out) = run_cmd([SUDO_PATH, REBOOT_PATH], "Reboot")
        ret = out
      elif c == 'apt update':
        (res, out) = run_cmd([SUDO_PATH, APT_PATH, 'update'], "Apt update")
        if res == 0:
          ret = "Apt update:\n%s" % out
        else:
          ret = out
      elif c == 'apt upgrade':
        (res, out) = run_cmd([SUDO_PATH, APT_PATH, 'upgrade', '-y'], "Apt upgrade", maxlines=12)
        if res == 0:
          ret = "Apt upgrade:\n%s" % out
        else:
          ret = out
      else:
        ret = "Command not implemented:\n%s" % cmd
    else:
      ret = "Unknown command:\n%s" % cmd
    return ret

command_list.append({
    'name' : 'Commands',
    'check': check,
    'run': run
})
