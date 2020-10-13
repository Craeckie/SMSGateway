import os, sys
from appdirs import *
import importlib.util

KEY = None

CONFIG_DIR = os.getenv('CONFIG_DIR', default=user_config_dir(appname="smsgateway", appauthor="craeckie"))
if not os.path.exists(CONFIG_DIR):
    os.mkdir(CONFIG_DIR)

_config_file = os.path.join(CONFIG_DIR, "config.py")
if not os.path.exists(_config_file):
    print("Error: no config file at %s!" % _config_file)
    sys.exit(1)


Messengers = []

sys.path.append(CONFIG_DIR)
from config import *
