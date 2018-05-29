# General Settings
CONTROL_PHONES = ['4912312312312',]

LOG_DIR = '/var/log/smsgateway/'

SMS_DIR = '/var/spool/sms/outgoing/'

SYSTEMCTL_PATH = '/bin/systemctl' # Use 'which systemctl' to find out
REBOOT_PATH = '/sbin/reboot'
APT_PATH = '/usr/bin/apt'
SUDO_PATH = '/usr/bin/sudo'

# Telegram
TELEGRAM_CLI_PATH = '/home/smsd/tg/bin/telegram-cli'
TELEGRAM_KEY_PATH = '/home/smsd/tg/tg-server.pub'
TG_USER_ID = 123123123

# Signal
SIGNAL_NUMBER = '+4912312312312'
SIGNAL_CLI_PATH = '/usr/local/bin/signal-cli'

# Facebook
FB_COOKIE_PATH = '/home/smsd/facebook-session.txt'
FB_CREDENTIALS = ('me@example.com', 'mysecretpassword')

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
