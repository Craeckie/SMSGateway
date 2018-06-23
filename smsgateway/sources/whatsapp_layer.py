from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
from yowsup.layers.protocol_groups.protocolentities    import AddParticipantsIqProtocolEntity
from smsgateway import sink_sms
from smsgateway.config import *

IDENTIFIER = "WA"

class EchoLayer(YowInterfaceLayer):
    def __init__(self):
        super(EchoLayer, self).__init__()
        self.jidAliases = WA_USER_ALIASES
        self.gidAliases = WA_GROUP_ALIASES

    def jidToAlias(self, jid):
        for ajid, alias in self.jidAliases.items():
            if ajid == jid:
                return alias
        return jid
    def gidToAlias(self, jid):
        for ajid, alias in self.gidAliases.items():
            if ajid == jid:
                return alias
        return jid

    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
        #send receipt otherwise we keep receiving the same message over and over

        if True:
            print("Sending receipt")
            receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom(), 'read', messageProtocolEntity.getParticipant())

            #outgoingMessageProtocolEntity = TextMessageProtocolEntity(
            #    messageProtocolEntity.getBody(),
            #    to = messageProtocolEntity.getFrom())

            #self.toLower(receipt)
            #self.toLower(outgoingMessageProtocolEntity)
            t = messageProtocolEntity.getBody()
            f = messageProtocolEntity.getFrom(False)
            print("From: %s" % f)
            if f == WA_NUMBER:
               print("Message from myself!")
            s = f.split('-')[0]
            print("Split: %s" % s)
            alias = self.jidToAlias(s)
            print("Alias: %s" % alias)
            if messageProtocolEntity.isGroupMessage():
                print("Is group message")
                g = f.split('-')[1]
                g_alias = self.gidToAlias(g)
                alias += '@' + g_alias
            print("From: %s\nMessage: %s" % (alias, t))
            sink_sms.send(IDENTIFIER, t, f)

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", entity.getType(), entity.getFrom())
        print("Receipt: %s" % ack)
        self.toLower(ack)
