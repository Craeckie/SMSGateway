FROM python:alpine AS base
RUN apk add bash libffi && \
    apk add --virtual .build alpine-sdk libffi-dev openssl-dev && \
    pip install smsgateway && \
    apk del .build


FROM base AS smstools
RUN apk add smstools && \
    mkdir -p /var/log/smstools/smsd_stats /var/run/smstools && \
    chown smsd:smsd -R /var/log/smstools /var/run/smstools
ADD smsd.conf /etc/smsd.conf
ADD scripts/smshandler scripts/run-smstools.sh /usr/bin/
RUN chmod +x /usr/bin/smshandler /usr/bin/run-smstools.sh
CMD ["run-smstools.sh"]


FROM base as smsgateway
RUN adduser gateway -h /home/gateway -D -u 1000 && \
    mkdir -p /var/log/smsgateway && \
    chown gateway:gateway /var/log/smsgateway
USER gateway
