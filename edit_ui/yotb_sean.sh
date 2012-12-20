#!/bin/bash

# SEE ALSO: http://gunicorn.org/

# To make sure this runs at startup, do:
# update-rc.d tilestache-gunicorn.sh defaults

# Source the correct virtual environment
source /home/seanc/venvs/yotb/bin/activate

ADDRESS=0.0.0.0:8080
DIRNAME=/var/www/com.stamen.studio/yearofthebay/show/recent/edit_ui

PIDFILE="yotb-gunicorn.pid"
LOGFILE="yotb-gunicorn.log"
COMMAND="gunicorn --daemon --user www-data --workers 4 --bind $ADDRESS --log-file $LOGFILE"
COMMAND="gunicorn --daemon --workers 4 --bind $ADDRESS --log-file $LOGFILE"

cd $DIRNAME

start_server () {
  if [ -f $PIDFILE ]; then
    #pid exists, check if running
    if [ "$(ps -p `cat $PIDFILE` | wc -l)" -gt 1 ]; then
       echo "Server already running on ${ADDRESS}"
       return
    fi
  fi
  echo "starting ${ADDRESS}"
  $COMMAND --pid $PIDFILE app:app
}

stop_server () {
  if [ -f $PIDFILE ] && [ "$(ps -p `cat $PIDFILE` | wc -l)" -gt 1 ]; then
    echo "stopping server ${ADDRESS}"
    kill -9 `cat $PIDFILE`
    rm $PIDFILE
  else
    if [ -f $PIDFILE ]; then
      echo "server ${ADDRESS} not running"
    else
      echo "No pid file found for server ${ADDRESS}"
    fi
  fi
}

restart_server () {
  if [ -f $PIDFILE ] && [ "$(ps -p `cat $PIDFILE` | wc -l)" -gt 1 ]; then
    echo "gracefully restarting server ${ADDRESS}"
    kill -HUP `cat $PIDFILE`
  else
    if [ -f $PIDFILE ]; then
      echo "server ${ADDRESS} not running"
    else
      echo "No pid file found for server ${ADDRESS}"
    fi
  fi
}

case "$1" in
'start')
  start_server
  ;;
'stop')
  stop_server
  ;;
'restart')
  restart_server
  ;;
*)
  echo "Usage: $0 { start | stop | restart }"
  ;;
esac

exit 0

