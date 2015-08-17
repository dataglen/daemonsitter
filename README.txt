DataGlen DaemonSitter

INTRODUCTION
============
This is a simple tool for monitoring systemd daemons. The tool
contains two files:
1. daemonsitter.sh - an init.d script 
2. daemonsitter.py - a python script

This tool has been tested ONLY on Debian Stable (Jessie) that is
running systemd and Python 2.7.

CONFIGURATION
=============
Both the aforementioned files require certain configuration parameters
to be specified as explained below.

daemonsitter.sh
---------------
The directory in which the python script is stored must be specified
as the DIR parameter.

daemonsitter.py
---------------
A number of configuration options are available. They are divided into
two sections - required parameters and optional parameters. The
optional parameter can be left to default values. But, the required
parameters MUST be specified.

INSTALLATION
============
As of now, there is now automatic installation mechanism. Will add
such features, if there is interest from the community in using this
tool.

daemonsitter.sh
---------------
This script must be placed in /etc/init.d directory and must be added
as a system init script using update-rc.d. Since this script must stop
before all the other daemons and start after all the other daemons,
update-rc.d may show a number of reordering requirements. 

daemonsitter.py
---------------
This script must be placed in the directory specified in the
daemonsitter.sh. Ideally the file must be readable and writeable only
by the root since the mail server id and password are specified in the
configuration section.

QUESTIONS?
==========
Please feel free to write to contact@dataglen.com. 


THANK YOU!


