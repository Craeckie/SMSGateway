import subprocess, re
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
