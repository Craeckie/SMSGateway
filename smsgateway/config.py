import os, sys
from appdirs import *
import importlib.util

CONFIG_DIR = user_config_dir(appname="smsgateway", appauthor="craeckie")
if not os.path.exists(CONFIG_DIR):
    os.mkdir(CONFIG_DIR)

_config_file = os.path.join(CONFIG_DIR, "config.py")
if not os.path.exists(_config_file):
    print("Error: no config file at %s!" % _config_file)
    sys.exit(1)

sys.path.append(CONFIG_DIR)
from config import *
