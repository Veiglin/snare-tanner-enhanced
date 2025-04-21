FROM alpine:3.19
#
# Include dist
COPY docker/snare/dist/ /root/dist/
#
# Include snare
COPY snare/ /opt/snare/
#
# Install packages
RUN apk -U upgrade && \
    apk -U add \
		build-base \
		git \
		linux-headers \
		python3 \
		python3-dev \
		py3-aiohttp \
		py3-beautifulsoup4 \
		py3-gitpython \
		py3-jinja2 \
		py3-markupsafe \
		py3-setuptools \
		py3-pip \
		py3-pycodestyle \
        py3-yaml \
		py3-wheel && \
#
# Setup Snare 
    cd /opt/snare/ && \
    cp /root/dist/requirements.txt . && \
    pip3 install --break-system-packages -r requirements.txt && \
    python3 setup.py install && \
    cd / && \
    rm -rf /opt/snare && \
    mkdir -p /opt/snare/pages && \
    cp /root/dist/config.yaml /opt/snare/ && \
    mv /root/dist/pages/* /opt/snare/pages/ && \
#
# Setup configs, user, groups
    addgroup -g 2000 snare && \
    adduser -S -s /bin/ash -u 2000 -D -g 2000 snare && \
    mkdir /var/log/tanner && \
    mkdir /var/log/snare && \
    chown -R snare:snare /opt/snare /var/log/snare && \
    mkdir -p /opt/snare-internal && \
    cp /root/dist/start_snare.py /opt/snare-internal/ && \
    chown snare:snare /opt/snare-internal/start_snare.py && \
    chmod 500 /opt/snare-internal/start_snare.py && \
#   
# Clean up
    apk del --purge \
            build-base \
            linux-headers \
            python3-dev && \
    rm -rf /root/* \
           /tmp/* /var/tmp/* \
           /var/cache/apk/*
#
# Start snare
STOPSIGNAL SIGKILL
USER snare:snare
# CMD ["python3", "/opt/snare-internal/start_snare.py"]
CMD snare --tanner tanner --debug true --auto-update false --host-ip 0.0.0.0 --port 443 --page-dir smartgadgetstore1 --breadcrumbs robots
