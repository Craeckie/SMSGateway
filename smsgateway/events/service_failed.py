from smsgateway import sink_sms
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("unit",
                            help="The unit that failed")
args = parser.parse_args()

msg = "%s failed, restarting.." % args.unit
print("Sending SMS:\n%s" % msg)
sink_sms.send_notif(msg)
