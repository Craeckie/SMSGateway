# SMSGateway

The following instructions apply to a Raspberry PI running Ubuntu, but it should work similarly on other Linux distributions and platforms.

## Configuration
Copy `smsgateway/config.example.py` to `smsgateway/config.py` and configure it. Most of the values should be self-explaining.

```bash
apt install smstools autossh
touch /var/log/smshandler.log && chown smsd:smsd /var/log/smshandler.log
mkdir /var/log/smsgateway/ && chown -R smsd:smsd /var/log/telegram/
```

## Telegram
Uses [Telegram-Cli](https://github.com/vysheng/tg) using [this](https://github.com/a-x-/tgl/tree/patch-1) patch to fix authorization
```bash
apt install libevent-dev libssl-dev libreadline-dev libconfig-dev liblua50-dev libjansson-dev
git clone --depth 1 https://github.com/vysheng/tg.git
cd tg
git clone --recursive https://github.com/a-x-/tgl.git
git checkout --depth 1 patch-1
./configure && make
```
## Facebook
Uses [fbchat](https://github.com/carpedm20/fbchat), see [documentation](https://fbchat.readthedocs.io/)
```bash
sudo apt install python3-dev libxml2-dev libxslt-dev
sudo pip install fbchat
```

## Signal
Uses [signal-cli](https://github.com/AsamK/signal-cli)
```bash
sudo apt install openjdk-8-jre-headless
wget https://github.com/AsamK/signal-cli/releases/download/v0.5.6/signal-cli-0.5.6.tar.gz
sudo tar xvf signal-cli-*.tar.gz -C /opt
sudo ln -svf /opt/signal-cli-"${VERSION}"/bin/signal-cli /usr/local/bin/
signal-cli link
```

## WhatsApp
Uses [Yowsup](https://github.com/tgalal/yowsup)
```bash
sudo pip install yowsup
# TODO
```
