#!/bin/sh
for d in outgoing checked incoming failed; do
  mkdir "/var/spool/sms/$d"
done
exec smsd -t
