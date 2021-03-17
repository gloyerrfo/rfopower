#!/bin/sh
#
# the running version is a link to this file at /usr/local/bin
r=`ps -ef | grep rfopower | grep -v grep | grep -vc run-rfopower`
if [ "$r" -eq 0 ] ; then
  /home/pi/Projects/ekm/rfopower 2>&1 &
  echo "rfopower started"
else
  echo "rfopower is already running"
fi
exit 0
