FROM alpine:3.17
#
# Include dist
COPY docker/tanner/dist/ /root/dist/
#
# Include snare
COPY tanner/ /opt/tanner/
#
# Install packages
RUN apk -U upgrade && \
    apk -U add \
		build-base \
		git \
		libcap \
		libffi-dev \
		openssl-dev \
		linux-headers \
		py3-aiohttp \
		py3-geoip2 \
		py3-jinja2 \
		py3-jwt \
		py3-mako \
		py3-mysqlclient \
		py3-packaging \
		py3-pip \
		py3-redis \
		py3-pycodestyle \
		py3-setuptools \
		py3-tornado \
		py3-websocket-client \
		py3-wheel \
		py3-yaml \
		py3-yarl \
		python3 \
		python3-dev && \ 
#
# Setup Tanner
	cd /opt/tanner/ && \
    cp /root/dist/config.yaml /opt/tanner/tanner/data && \
    cp /root/dist/requirements.txt . && \
    pip3 install -r requirements.txt && \
    python3 setup.py install && \
    rm -rf .coveragerc \
           .git \
           .gitignore \
           .travis.yml \
           Tanner.egg-info \
           build \
           dist \
           docker \
           docs \
           requirements.txt \
           setup.py && \
    cd / && \
#   
# Setup configs, user, groups
    addgroup -g 2000 tanner && \
    adduser -S -s /bin/ash -u 2000 -D -g 2000 tanner && \
    mkdir -p /var/log/tanner && \
    touch /var/log/tanner/tanner.err && \
    chown -R tanner:tanner /opt/tanner /var/log/tanner && \
    chmod -R 755 /var/log/tanner && \
# Clean up
    apk del --purge \
            build-base \
            git \
            libcap \
            libffi-dev \
            openssl-dev \
            linux-headers \
            python3-dev && \
    rm -rf /root/* \
           /tmp/* \
           /var/tmp/* \
           /var/cache/apk/* \
           /opt/tanner/.git
#
# Start tanner
STOPSIGNAL SIGKILL
USER tanner
WORKDIR /opt/tanner
CMD tanner 
