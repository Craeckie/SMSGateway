import logging

# General Settings
CONTROL_PHONES = ['4912312312312', ]

LOG_DIR = '/var/log/smsgateway/'
LOG_STD_LEVEL = logging.DEBUG

SMS_DIR = '/var/spool/sms/outgoing/'

SYSTEMCTL_PATH = '/bin/systemctl'  # Use 'which systemctl' to find out
REBOOT_PATH = '/sbin/reboot'
# When using a ramdisk you can use the script instead (see README):
REBOOT_PATH = '/usr/local/bin/pi-reboot'
APT_PATH = '/usr/bin/apt'
SUDO_PATH = '/usr/bin/sudo'

# Encryption
# Generate with python -c 'from cryptography.fernet import Fernet as f; print(f.generate_key())'
KEY = "xyz="

Messengers = [
    {  # Signal
        'Type': 'SG',
        'Number': '+4912312312312',
        'CLI_Path': '/usr/local/bin/signal-cli',
    },
    {  # Facebook
        'Type': 'FB',
        'Cookie_Path': '/home/smsd/facebook-session.txt',
        'Username': 'me@example.com',
        'Password': 'mysecretpassword',
    },
    {  # Slack
        'Type': 'SL',
        'Identifier': 'SL1',
        'Token': 'xxxx',
    },
    {  # E-Mail
        'Type': 'EM',
        'Host': 'imap.example.com',
        'User': 'somebody@example.com',
        'Password': 'mysecretpassword',
    },
    {  # WhatsApp
        'Type': 'WA',
        'Number': '4912312312312',
        'User_Aliases': {
            '4912312312312': 'Friend 1',
            '4912312312313': 'Friend 2'
        },
        'Group_Aliases': {
            '123123123': 'Group 1',
            '123123123123': 'Group 2'
        },
    }
]

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
