# SMSGateway

This project is in Alpha stage, so expect bugs. Pull requests welcome!

The following instructions apply to a Raspberry PI running Ubuntu, but it should work similarly on other Linux distributions and platforms.
Some commands might require to be invoked with `sudo`.

See [SMSGateway-Android](https://github.com/Craeckie/SMSGateway-Android) for an Android client.

## Configuration
```bash
git clone https://github.com/Craeckie/SMSGateway.git
```
Copy `smsgateway/config.example.py` to `smsgateway/config.py` and adapt it, then install it:
```bash
python3 setup.py install
```
### Logging
`mkdir /var/log/smsgateway/ && chown -R smsd:smsd /var/log/smsgateway/`

### SMS Tools
Install [smstools](smstools3.kekekasvi.com):
```bash
apt install smstools
```
Edit `/etc/smsd.conf`, see `Confiuration/smsd.conf` for an example configuration.

### Handle SMS messages
Copy `Scripts/smshandler` to `/usr/local/bin/` and make executable:
`chmod +x /usr/local/bin/smshandler`

### Permission to control systemctl, shutdown, etc.
Copy `Configuration/010_smsd-nopasswd` to `/etc/sudoers.d/`

Make sure that the file is correct, otherwise you might **lock yourself out**! If you're unsure, run
`visudo -f /etc/sudoers.d/010_smsd-nopasswd`, enter the contents in the editor and save it.

### Telegram
Uses [Telegram-Cli](https://github.com/vysheng/tg) using [this](https://github.com/a-x-/tgl/tree/patch-1) patch to fix authorization
```bash
apt install libevent-dev libssl-dev libreadline-dev libconfig-dev liblua50-dev libjansson-dev
git clone --depth 1 https://github.com/vysheng/tg.git
cd tg
git clone --recursive https://github.com/a-x-/tgl.git
git checkout --depth 1 patch-1
./configure && make
```
### Facebook
Uses [fbchat](https://github.com/carpedm20/fbchat), see [documentation](https://fbchat.readthedocs.io/)
```bash
sudo apt install python3-dev libxml2-dev libxslt-dev
sudo pip install fbchat
```

### Signal
Uses [signal-cli](https://github.com/AsamK/signal-cli)
```bash
sudo apt install openjdk-8-jre-headless
wget https://github.com/AsamK/signal-cli/releases/download/v0.5.6/signal-cli-0.5.6.tar.gz
sudo tar xvf signal-cli-*.tar.gz -C /opt
sudo ln -svf /opt/signal-cli-"${VERSION}"/bin/signal-cli /usr/local/bin/
signal-cli link
```

### WhatsApp
Uses [Yowsup](https://github.com/tgalal/yowsup)
```bash
sudo pip install yowsup
# TODO
```
