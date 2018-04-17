from yowsup.stacks import  YowStackBuilder
from smsgateway.sources.whatsapp_layer import EchoLayer
from yowsup.layers.auth import AuthError
from yowsup.layers import YowLayerEvent
from yowsup.layers.network import YowNetworkLayer
from yowsup.env import YowsupEnv
import argparse

#credentials = ("4912312312312", "aBcD123=") # replace with your phone and password

if __name__==  "__main__":
    parser = argparse.ArgumentParser(description='Listen to WhatsApp messages')
    parser.add_argument('phone', help='Your phone number with country code')
    parser.add_argument('password', help='The password you obtained with yowsup-cli registration')
    args = parser.parse_args()
    credentials = (args.phone, args.password)

    print("Building stack..")
    stackBuilder = YowStackBuilder()

    stack = stackBuilder\
        .pushDefaultLayers(True)\
        .push(EchoLayer)\
        .build()

    stack.setCredentials(credentials)
    stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))   #sending the connect signal
    print("Starting loop..")
    stack.loop() #this is the program mainloop
