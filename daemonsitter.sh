#!/bin/sh

# Copyright [2015] [DataGlen]

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

### BEGIN INIT INFO
# Provides:          daemonsitter
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: DataGlen Daemonsitter
# Description:       This daemon watches a list of daemons specified 
#                    in the python file.
### END INIT INFO

# Change the next 3 lines to suit where you install your script and what you want to call it
DIR=/opt/dataglen
DAEMON=$DIR/daemonsitter.py
DAEMON_NAME=daemonsitter

# This next line determines what user the script runs as.
DAEMON_USER=root

. /lib/lsb/init-functions

do_start () {
    log_daemon_msg "Starting daemon" "$DAEMON_NAME"
    python $DAEMON start
    log_end_msg $?
}

do_stop () {
    log_daemon_msg "Stopping daemon" "$DAEMON_NAME"
    python $DAEMON stop
    log_end_msg $?
}

case "$1" in

    start|stop)
        do_${1}
        ;;

    restart|reload|force-reload)
        do_stop
        do_start
        ;;

    *)
        echo "Usage: /etc/init.d/$DAEMON_NAME {start|stop|restart}"
        exit 1
        ;;
esac

exit 0