# SMSGateway

This project is in Beta stage, so documentation is quite limited. Pull requests welcome!

The following instructions apply to a Raspberry PI running Ubuntu, but it should work similarly on other Linux distributions and platforms.
Some commands might require to be invoked with `sudo`.

See [SMSGateway-Android](https://github.com/Craeckie/SMSGateway-Android) for an Android client.

## SMS Tools
Install [smstools](smstools3.kekekasvi.com):
```bash
apt install smstools
```
Edit `/etc/smsd.conf`, see `Confiuration/smsd.conf` for an example configuration.
It uses to user `smsd` for the sms spooler at `/var/spool/sm`s.

## Configuration
```bash
pip install smsgateway
```
Copy `smsgateway/config.example.py` to `/home/smsd/.config/smsgateway/config.py` and adapt it.

## Handle incoming SMS
To handling incoming sms `Scripts/smshandler` needs to be copied to the `eventhandler` specified in `smsd.conf`. In the example it points to `/usr/local/bin/smshandler`.

Make sure to make it executable (`chmod +x`).

### Logging
`mkdir /var/log/smsgateway/ && chown -R smsd:smsd /var/log/smsgateway/`

### Permission to control systemctl, shutdown, etc.
Copy `Configuration/010_smsd-nopasswd` to `/etc/sudoers.d/`

Make sure that the file is correct, otherwise you might **lock yourself out**! If you're unsure, run
`visudo -f /etc/sudoers.d/010_smsd-nopasswd`, enter the contents in the editor and save it.

## Messengers

### Telegram
Uses [Telethon](https://github.com/LonamiWebs/Telethon).

Run `python3 -m smsgateway.sources.telegram` to authorize for receiving messages, similarly run `python3 -m smsgateway.sources.commands.send_telegram` to authorize for sending messages.

### Facebook
Uses [fbchat](https://github.com/carpedm20/fbchat), see [documentation](https://fbchat.readthedocs.io/)
```bash
apt install python3-dev libxml2-dev libxslt-dev
pip install fbchat
```

### Signal
Uses [signal-cli](https://github.com/AsamK/signal-cli)
```bash
SGVER="0.6.2"
apt install openjdk-8-jre-headless
wget "https://github.com/AsamK/signal-cli/releases/download/v$SGVER/signal-cli-$SGVER.tar.gz"
tar xvf "signal-cli-$SGVER.tar.gz" -C /opt
ln -svf "/opt/signal-cli-${SGVER}/bin/signal-cli" /usr/local/bin/
signal-cli link
# You can remove old versions at /opt/signal-cli-<version>
```

### Slack
Go to https://api.slack.com/custom-integrations/legacy-tokens
Sign in, create a token and store it in your configuration at `SL_TOKEN`

### WhatsApp
Uses [Yowsup](https://github.com/tgalal/yowsup)
```bash
pip install yowsup
# TODO
```

## Tweaks and optimizations

### Ramdisk for SMS
When lots of SMS are processed it can wear out SD cards (I destroyed one after several months).
A workaround is to store the SMS messages in a ramdisk. The following is an entry in the fstab:
```
tmpfs   /var/spool/sms  tmpfs         nodev,nosuid,size=64M     0       0
```
To mount it simply call `mount /var/spool/sms`.

The downside is, that when the device restarts/crashed, currently processed SMS messages are lost.
To work around that there are two scripts for saving&restoring the messages in `Scripts/` and a oneshot-service, which can be enabled to restore the message when the device is starting.
