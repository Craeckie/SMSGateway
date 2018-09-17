import subprocess, re, os
import gzip, shutil
from smsgateway.config import *

def _logging_namer(name):
    return name + ".gz"
def _logging_rotater(source, dest):
    with open(source, "rb") as sf:
        # data = sf.read()
        # compressed = zlib.compress(data, 9)
        with gzip.open(dest, 'wb') as df:
            shutil.copyfileobj(sf, df)
    os.remove(source)

def setup_logging(service_name):
    import logging
    from logging import StreamHandler
    from logging.handlers import RotatingFileHandler

    filelog_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    syslog_formatter = logging.Formatter('%(message)s')
    logFile = os.path.join(LOG_DIR, f"{service_name}.log")
    file_handler = RotatingFileHandler(logFile, mode='a', maxBytes=20*1024*1024,
                                     backupCount=5, encoding=None, delay=0)
    file_handler.rotator = _logging_rotater
    file_handler.namer = _logging_namer
    file_handler.setFormatter(filelog_formatter)
    file_handler.setLevel(logging.DEBUG)

    std_handler = StreamHandler(sys.stdout)
    std_handler.setFormatter(syslog_formatter)
    std_handler.setLevel(LOG_STD_LEVEL)

    app_log = logging.getLogger('root')
    app_log.setLevel(logging.DEBUG)
    app_log.addHandler(file_handler)
    app_log.addHandler(std_handler)
    return app_log

def run_cmd(args, name=None, maxlines=7, timeout=300):
    success = True
    try:
      res = subprocess.check_output(args, stderr=subprocess.STDOUT, timeout=timeout).decode('UTF-8').strip()
    except subprocess.CalledProcessError as e:
      success = False
      if name:
        res = "%s:\nError: %s\n%s" % (name, e, e.output.decode('UTF-8').strip())
      else:
        res = "Error %s:\n%s" % (e, e.output.decode('UTF-8').strip())
    except subprocess.TimeoutExpired as e:
      success = False
      if name:
        res = "%s:\nError: Timeout when calling Process:\n%s\n%s" % (name, e, e.output.decode('UTF-8').strip())
      else:
        res = "Error %s:Timeout when calling Process:\n%s" % (e, e.output.decode('UTF-8').strip())
    res = '\n'.join([x for x in res.split('\n') if x][:maxlines])
    return (success, res)

def _repl(regex, sub, text):
  return re.sub(regex, sub, text, flags=re.UNICODE)

def format_sms(type, text, headers):
    msg = f"{type}\n"
    msg += '\n'.join([f"{k[0].upper() + k[1:]}: {v}" for k,v in headers.items() if len(k) > 1])
    if text:
        msg += f"\n\n{text}"
    return msg

try:
  import emoji
  use_emoji = True
except ModuleNotFoundError:
  use_emoji = False

def replaceEmoticons(text):
  text = _repl(r'\U0001F60A', ':-)', text)
  text = _repl(r'\U0001F914', ':-?', text)
  # text = _repl(r'\U0001F602', ':-D', text)
  text = _repl(r'\U0001F604', ':-D', text)
  if use_emoji:
    return emoji.demojize(text)
  else:
    return text

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
