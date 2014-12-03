#!/usr/bin/env bash
if [[ $EUID -ne 0 ]]; then
    echo "You must be a root user to set these permissions"
    exit 1
fi

if [ "$#" -ne 1 ]; then
  export ATMOSPHERE_HOME="$1"
else
  export ATMOSPHERE_HOME=/opt/dev/atmosphere
fi

chmod -R g+w ${ATMOSPHERE_HOME}

chmod -R 644 ${ATMOSPHERE_HOME}/extras/ssh

chmod 755 ${ATMOSPHERE_HOME}/extras/ssh

chmod -R 600 ${ATMOSPHERE_HOME}/extras/ssh/id_rsa

chown -R www-data:www-data ${ATMOSPHERE_HOME}

chown -R www-data:www-data ${ATMOSPHERE_HOME}/extras/apache

chown -R root:root ${ATMOSPHERE_HOME}/extras/ssh

