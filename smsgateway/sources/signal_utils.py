import subprocess
from time import sleep

from smsgateway.config import *


def connect(app_log, session_path):
    proc = subprocess.Popen([
            SIGNAL_CLI_PATH,
            '--config', session_path,
            '-u', SIGNAL_NUMBER,
            'listDevices',
        ],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    wait_counter = 0
    poll_interval = 0.1
    while proc.poll() == None and wait_counter < 5 / poll_interval:
        sleep(poll_interval)
        wait_counter += 1
    p = proc.poll()
    (std, err) = proc.communicate(None)
    if err:
        err_dec = err.decode('UTF-8')
        app_log.info(err_dec)
        if err_dec == "User is not registered.\n" or err_dec.startswith('Authorization failed, was the number registered elsewhere?'): # need to link device
            app_log.warning("Need to link first, getting URL..")
            proc = subprocess.Popen([
                SIGNAL_CLI_PATH,
                '--config', session_path,
                'link',
                '-n', 'pi'
            ],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            url = proc.stdout.readline().decode('UTF-8').replace('\n', '')
            if url.startswith("tsdevice:/"):
                app_log.info(url)
                app_log.info(f"You can create a QR to scan with your phone using qrencode -l Q -s 5 -o qrcode.png \"{url}\"")
            else:
                app_log.warning("Request failed!")
            (std, err) = proc.communicate()
            std_dec = std.decode('UTF-8')
            err_dec = std.decode('UTF-8')
            if std_dec.startswith('Associated with'):
                return True
            else:
                app_log.error("Linking failed!")
                app_log.error(std_dec)
                app_log.error(err_dec)
                return False
        else:
            app_log.info("Got some unknown message, trying to continue..")
            return True

    else:
        return True
