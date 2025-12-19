#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null && pwd)"

# If you are using transmission-daemon directly on system the below code will ensure that trackers script run only when it is running
if [ "$(systemctl is-active transmission-daemon)" = "active" ]
then
/usr/bin/python3 $DIR/transmission-trackers.py
fi

# If you are using docker for transmission use the following. Replace 'docker-container-name' with the appropriate name and uncomment the following
#if [ "$( docker container inspect -f '{{.State.Running}}' 'docker-container-name' )" = "true" ]
#then
#/usr/bin/python3 $DIR/transmission-trackers.py
#fi
