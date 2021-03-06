import logging

# General Settings
CONTROL_PHONES = ['4912312312312',]

LOG_DIR = '/var/log/smsgateway/'
LOG_STD_LEVEL = logging.DEBUG

SMS_DIR = '/var/spool/sms/outgoing/'

SYSTEMCTL_PATH = '/bin/systemctl' # Use 'which systemctl' to find out
REBOOT_PATH = '/sbin/reboot'
# When using a ramdisk you can use the script instead (see README):
# REBOOT_PATH = '/usr/local/bin/pi-reboot'
APT_PATH = '/usr/bin/apt'
SUDO_PATH = '/usr/bin/sudo'

# Encryption
# Generate with python -c 'from cryptography.fernet import Fernet as f; print(f.generate_key())'
KEY = "xyz="

# Matrix
MATRIX_CREDENTIALS = ('@me:matrix.org', 'mysecretpassword')
MATRIX_HS_URL = "https://matrix.org"

# Telegram
TELEGRAM_CLI_PATH = '/home/smsd/tg/bin/telegram-cli'
TELEGRAM_KEY_PATH = '/home/smsd/tg/tg-server.pub'
TG_USER_ID = 164387030

# Signal
SIGNAL_NUMBER = '+4912312312312'
SIGNAL_CLI_PATH = '/usr/local/bin/signal-cli'

# Facebook
FB_COOKIE_PATH = '/home/smsd/facebook-session.txt'
FB_CREDENTIALS = ('me@example.com', 'mysecretpassword')

# Slack
SL_TOKEN = 'xxxx'

# E-Mail
EMAIL_ACCOUNTS = {
    'example_name': {
      'Host': 'imap.example.com',
      'User': 'somebody@example.com',
      'Password': 'mysecretpassword'
    }
}

# WhatsApp
WA_NUMBER = '4912312312312'
WA_USER_ALIASES = {
    '4912312312312' : 'Friend 1',
    '4912312312313' : 'Friend 2',
    }

WA_GROUP_ALIASES = {
    '123123123' : 'Group 1',
    '123123123123' : 'Group 2',
    }

# Command settings
SERVICES = ['dhcpcd',
            'sane-forwards',
            'source-telegram',
            'source-whatsapp',
            'source-signal',
            'source-slack',
            'source-email',
            'source-facebook',
            'smstools',
            'wpa_supplicant',
            'ModemManager',
            'NetworkManager',
            ]

WIFI_INTERFACES_ALL = ['wlan0', 'wlan1']
NETWORK_INTERFACES_ALL = ['eth0'] + WIFI_INTERFACES_ALL
WIFI_INTERFACES = ['wlan0']
NETWORK_INTERFACES = ['eth0']
