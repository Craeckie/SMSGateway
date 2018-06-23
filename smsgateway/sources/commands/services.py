import re, subprocess
from smsgateway.sources.sms import command_list
from smsgateway.config import *

service_commands = ['start', 'restart', 'stop', 'enable', 'disable', 'status']
service_regex = re.compile('^(?P<command>[a-zA-Z]+) (?P<service>.+)$')


def run_cmd(args):
    return subprocess.check_output(args, stderr=subprocess.STDOUT).decode('UTF-8').strip()

def match(cmd):
    m = service_regex.match(cmd)
    c = m.groupdict()['command']
    s = m.groupdict()['service']
    return (c, s)

def check(cmd, multiline):
    # print("Checking %s" % cmd)

    if service_regex.match(cmd):
      print("Service RE matches!")
      (c, s) = match(cmd)
      if c in service_commands and s in SERVICES:
        print("Command: %s, Service: %s" % (c, s))
        return True
    return False
def run(lines):
    cmd = lines[0]
    (c, s) = match(cmd)

    if c in service_commands and s in SERVICES:
      try:
        out = run_cmd([SUDO_PATH, SYSTEMCTL_PATH, c, s])

        ret = "%s: OK!\n%s" % (cmd, out)
      except subprocess.CalledProcessError as e:
        ret = "%s failed:\n%s" % (cmd, e.output.decode('UTF-8').strip())
    else:
      ret = "Unknown command or service:\n%s" % cmd
    return ret

command_list.append({
    'name' : 'Services',
    'check': check,
    'run': run
})
