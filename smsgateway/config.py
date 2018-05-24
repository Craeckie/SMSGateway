import os, sys
from appdirs import *
import importlib.util

_config_dir = user_config_dir(appname="smsgateway", appauthor="craeckie")
if not os.path.exists(_config_dir):
    os.mkdir(_config_dir)

_config_file = os.path.join(_config_dir, "config.py")
if not os.path.exists(_config_file):
    print("Error: no config file at %s!" % _config_file)
    sys.exit(1)

sys.path.append(_config_dir)
from config import *
