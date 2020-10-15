#!/bin/sh
for d in outgoing checked incoming failed; do
  mkdir "/var/spool/sms/$d"
  chown smsd:smsd -R /var/spool/sms/
done
exec smsd -t
