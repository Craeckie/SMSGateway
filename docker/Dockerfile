FROM python:alpine3.12 AS base
RUN apk add bash libffi openssl olm && \
    apk add --virtual .build alpine-sdk libffi-dev cargo openssl-dev olm-dev && \
    pip install --upgrade pip setuptools && \
    pip install --pre smsgateway && \
    apk del .build


FROM base AS smstools
RUN apk add smstools && \
    mkdir -p /var/log/smstools/smsd_stats /var/run/smstools && \
    chown smsd:smsd -R /var/log/smstools /var/run/smstools
ADD smsd.conf /etc/smsd.conf
ADD scripts/smshandler scripts/run-smstools.sh /usr/bin/
RUN chmod +x /usr/bin/smshandler /usr/bin/run-smstools.sh
RUN mkdir -p /var/log/smsgateway && \
    chown smsd:smsd /var/log/smsgateway
CMD ["run-smstools.sh"]


#adduser gateway -h /home/gateway -D -u 100 && \
FROM base as smsgateway
RUN mkdir -p /var/log/smsgateway && \
    chown 100:100 /var/log/smsgateway
USER 100
