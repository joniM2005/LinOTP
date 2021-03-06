# -*- coding: utf-8 -*-
#
#    LinOTP - the open source solution for two factor authentication
#    Copyright (C) 2016 KeyIdentity GmbH
#
#    This file is part of LinOTP server.
#
#    This program is free software: you can redistribute it and/or
#    modify it under the terms of the GNU Affero General Public
#    License, version 3, as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the
#               GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#    E-mail: linotp@lsexperts.de
#    Contact: www.linotp.org
#    Support: www.lsexperts.de
#
#
# LinOTP Docker build script

FROM debian:jessie

ARG DEBIAN_MIRROR=deb.debian.org
ARG LINOTP_MIRROR=www.linotp.org

# The following environment variables can be set to
# configure the runtime behaviour of the container.
# Most of these should be self explanitory.
#
# To disable HTTP authentication for the manage UI,
# set LINOTP_APACHE_AUTH=false.
#
# To serve via HTTP instead of HTTPS:
#  LINOTP_APACHE_SSL=false
#  APACHE_PORT=80
#
# To use a MySQL database:
#  LINOTP_DB_TYPE=mysql
# and also substitute suitable values:
#  LINOTP_DB_HOST=hostname
#  LINOTP_DB_PORT=3306
#  LINOTP_DB_USER=user
#  LINOTP_DB_PASSWORD=password
#  LINOTP_DB_NAME=database-name
#
# To allow unencrypted healthcheck by
# checking /validate/ok, set
#  HEALTHCHECK_PORT=<port>
#
# To send LinOTP logs directly to
# Logstash, set LOGSTASH_HOST and
# LOGSTASH_PORT to point to your
# Logstash collector. You can optionally
# add additional tags with the
# LOGSTASH_TAGS setting. This is a Python
# list. For example:
#   LOGSTASH_HOST=logstash1
#   LOGSTASH_PORT=5000
#   LOGSTASH_TAGS=('instance1', 'server1')

ENV LINOTP_USER=linotp \
	LINOTP_DB_TYPE=sqlite \
	LINOTP_DB_NAME=//tmp/linotp.db \
	LINOTP_DB_HOST=dbhost \
	LINOTP_DB_PORT=3306 \
	LINOTP_DB_USER=dbuser \
	LINOTP_DB_PASSWORD=dbpass \
	LINOTP_ADMIN_USER=admin \
	LINOTP_ADMIN_PASSWORD=admin \
	LINOTP_APACHE_AUTH=true \
	LINOTP_APACHE_SSL=true \
	APACHE_PORT=443 \
	APACHE_LOGLEVEL=info \
	HEALTHCHECK_PORT= \
	LOGSTASH_HOST= \
	LOGSTASH_PORT= \
	LOGSTASH_TAGS=()

# Internal environment variables used by the docker images
ENV LINOTP_INI_TEMPLATE=/etc/linotp/linotp-docker.ini.tmpl \
	LINOTP_HOME=/opt/linotp \
	DEBIAN_FRONTEND=noninteractive

RUN echo 'APT::Install-Recommends "0"; \n\
			APT::Get::Assume-Yes "true"; \n\
			APT::Install-Suggests "0";' \
		> /etc/apt/apt.conf.d/01buildconfig

RUN sed "s#http://deb\.debian\.org/#http://${DEBIAN_MIRROR}/#" \
    < /etc/apt/sources.list > /etc/apt/sources.list.new && mv -f /etc/apt/sources.list.new /etc/apt/sources.list

# Add LinOTP packaging key to keyring in order to install
# dependencies
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 \
		--recv-keys 913DFF12F86258E5

# Install some dependencies which will be cached. This does not
# need to be an exhaustive list because apt will install any
# missing packages.
RUN \
    echo "deb http://${LINOTP_MIRROR}/apt/debian jessie linotp" > /etc/apt/sources.list.d/linotp.list \
    && apt-get update \
    && extraPackages=' \
	make \
	python-psycopg2 \
    ' \
    && apt-get install \
		$extraPackages \
		adduser debconf openssl pwgen python-beaker python-configobj \
		python-decorator python-docutils python-formencode python-httplib2 \
		python-ldap python-m2crypto python-mako python-mysqldb python-netaddr \
		python-paste python-pastedeploy python-pastescript python-pygments python-pylons \
		python-pyrad python-qrcode python-repoze.who python-routes python-simplejson \
		python-sqlalchemy python-tempita python-weberror python-webhelpers python-webob \
		apache2 libapache2-mod-wsgi python-pycryptodomex python-pysodium python-requests

# Install linotp packages from local files.
COPY apt /opt/linotp/apt

RUN echo "linotp linotp/apache/activate boolean true" > /opt/linotp/apt/debconf-selections \
	&& echo "linotp linotp/apache/ssl_create boolean true" >> /opt/linotp/apt/debconf-selections \
	&& debconf-set-selections /opt/linotp/apt/debconf-selections \
	&& echo "deb [trusted=yes] file:/opt/linotp/apt ./" > /etc/apt/sources.list.d/linotp-local.list \
	&& (echo "Package: *"; echo "Pin: origin \"\""; echo "Pin-Priority: 900") > /etc/apt/preferences.d/linotp \
	&& apt-get update \
	&& apt-get install linotp linotp-smsprovider linotp-useridresolver python-logstash \
	&& rm /etc/apt/sources.list.d/linotp-local.list \
	&& rm -r /opt/linotp/apt /etc/apache2/sites-enabled/000-default.conf \
	&& rm /etc/linotp2/linotp.ini /etc/linotp2/encKey /etc/linotp2/*.pem

WORKDIR $LINOTP_HOME

# Get dockerfy and configuration template files from build context
COPY *.tmpl /etc/linotp2/
COPY dockerfy /usr/local/bin/
COPY linotp-create-htdigest /usr/local/bin/
RUN chmod 755 /usr/local/bin/linotp-create-htdigest

ENTRYPOINT [ "/usr/local/bin/dockerfy", \
     "--template", "/etc/linotp2/linotp-docker.ini.tmpl:/etc/linotp2/linotp.ini", \
     "--template", "/etc/linotp2/apache-docker.conf.tmpl:/etc/apache2/sites-enabled/linotp2.conf", \
     "--run", "/var/lib/dpkg/info/linotp.postinst", "configure", "--", \
     "--run", "/bin/grep", "url", "/etc/linotp2/linotp.ini", "--", \
     "--run", "mkdir", "-p", "/etc/ssl/private", "/etc/ssl/certs", "--", \
     "--run", "/bin/sh", "-c", \
        "openssl req -new -x509 -newkey rsa:2048 -subj /CN=`hostname`.`dnsdomainname` -days 768 -out /etc/ssl/certs/linotpserver.pem  -keyout /etc/ssl/private/linotpserver.key -nodes", \
        "--", \
     "--run", "/usr/local/bin/linotp-create-htdigest", "{{ .Env.LINOTP_ADMIN_USER }}", "{{ .Env.LINOTP_ADMIN_PASSWORD }}", "--", \
     "--run", "/bin/sh", "-c", \
        "if [ {{ .Env.LINOTP_DB_TYPE }} != sqlite ]; then /usr/local/bin/dockerfy --wait tcp://{{ .Env.LINOTP_DB_HOST }}:{{ .Env.LINOTP_DB_PORT }} --timeout 30s; fi", \
        "--", \
     "--run", "/bin/su", "linotp", "-s", "/bin/sh", "-c", "paster setup-app /etc/linotp2/linotp.ini", "--" \
     ]

CMD [ \
	"/usr/sbin/apache2ctl", "-DFOREGROUND" \
	]

# Listen on apache port (https 443 by default - see LINOTP_APACHE_SSL and APACHE_PORT)
EXPOSE $APACHE_PORT
