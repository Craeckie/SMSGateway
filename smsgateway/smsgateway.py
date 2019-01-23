from smsgateway import config
from .sources import *

def __main__():
    for m in config.Messengers:
        t = m['type']