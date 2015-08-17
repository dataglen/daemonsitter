# Copyright [2015] [DataGlen]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from subprocess import call
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from smtplib import SMTPException
import logging
from daemon import runner
import sys
import signal
import socket
from validate_email import validate_email

# ========================== CONFIGURATION SECTION ============================
# ----------------------- BEGIN REQUIRED PARAMETERS----------------------------
# BEGIN REQUIRED PARAMETERS
# Deamons to be monitored. Specify a comma-separated list.
DAEMONS = ["apache2", "rabbitmq-server"]

MAIL_SERVER = ''  # example - "smtp.gmail.com"
MAIL_SERVER_UID = ''  # example - "name1@gmail.com"
MAIL_SERVER_PASSWORD = ''  # example - "secretword"
MAIL_RECEIVERS = []  # example - ["name2@yahoo.com", "name3@hotmail.com"]
MAIL_SENDER = ''  # example - "nameless@gmail.com"

# ----------------------- BEGIN OPTIONAL PARAMETERS----------------------------
LOG_FILE_NAME = "/var/log/dameonsitter.log"
PID_FILE = "/var/run/daemonsitter.pid"

# How often this program must check the health of aforementioned daemons
CHECKING_INTERVAL = 300  # in seconds
# How often this program must send emails to inform its status
HEARTBEAT_INTERVAL = 1500  # in seconds
# After restarting a daemon, how long should it wait to confirm
CONFIRM_INTERVAL = 120  # in seconds
# How many times it should attempt to restart
MAX_RETRIES = 3

# ========================== END OF CONFIGURATION SECTION =====================
SYSCTL_SUCCESS = 0
SUCCESS = 0
FAILURE = -1

the_daemon_object = None
the_logger = None

class DaemonSitter(object):
    def __init__(self):

        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path = PID_FILE
        self.pidfile_timeout = 5
        self.daemon_table = {}

        self.logger = logging.getLogger("DaemonSitter")
        self.logger.setLevel(logging.DEBUG)

        try:
            self.file_handler = logging.FileHandler(LOG_FILE_NAME)
            self.logger.addHandler(self.file_handler)
        except IOError:
            sys.exit(RuntimeError)

        self.last_message_time = datetime(2014, 11, 1)
        self.hostname = socket.gethostname()

        self.initialize()

        return

    def initialize(self):

        if not MAIL_SERVER_UID:
            self.logger.debug(str(datetime.now()) + ": " +
                              " MAIL_SERVER_UID parameter is blank.")
            sys.exit(RuntimeError)

        if not MAIL_SERVER_PASSWORD:
            self.logger.debug(str(datetime.now()) + ": " +
                              " MAIL_SERVER_PASSWORD parameter is blank.")
            sys.exit(RuntimeError)

        if not MAIL_SERVER:
            self.logger.debug(str(datetime.now()) + ": " +
                              " MAIL_SERVER parameter is blank.")
            sys.exit(RuntimeError)

        if not MAIL_SENDER:
            self.logger.debug(str(datetime.now()) + ": " +
                              " MAIL_SENDER parameter is blank.")
            sys.exit(RuntimeError)

        is_valid = validate_email(MAIL_SENDER, verify=True)
        if not is_valid:
            self.logger.debug(str(datetime.now()) + ": " +
                              " invalid_email address - " + MAIL_SENDER +
                              " - specified as the sender.")
            sys.exit(RuntimeError)

        if not MAIL_RECEIVERS:
            self.logger.debug(str(datetime.now()) + ": " +
                              " MAIL_RECEIVERS parameter is empty.")
            sys.exit(RuntimeError)

        for receiver in MAIL_RECEIVERS:
            is_valid = validate_email(receiver, verify=True)

            if not is_valid:
                self.logger.debug(str(datetime.now()) + ": " +
                                  " invalid_email address - " + receiver +
                                  " - specified in MAIL_RECEIVERS.")
                sys.exit(RuntimeError)

        if CHECKING_INTERVAL <= 0:
            self.logger.debug(str(datetime.now()) + ": " +
                              " CHECKING_INTERVAL must be a positive integer.")
            sys.exit(RuntimeError)

        if HEARTBEAT_INTERVAL <= 0:
            self.logger.debug(str(datetime.now()) + ": " +
                              " HEARTBEAT_INTERVAL must be a positive integer.")
            sys.exit(RuntimeError)

        if CONFIRM_INTERVAL <= 0:
            self.logger.debug(str(datetime.now()) + ": " +
                              " CONFIRM_INTERVAL must be a positive integer.")
            sys.exit(RuntimeError)

        if MAX_RETRIES <= 0:
            self.logger.debug(str(datetime.now()) + ": " +
                              " MAX_RETRIES must be a positive integer.")
            sys.exit(RuntimeError)

        for daemon in DAEMONS:
            daemon_info = {'retry_count': 0, 'notified': False, 'running': False}
            self.daemon_table[daemon] = daemon_info

        msg = "The DaemonSitter will monitor the following daemons: \n" + "\n".join(DAEMONS)
        self.send_mail(msg, "DataGlen DaemonSitter started on " + self.hostname + ".")

        self.logger.debug(str(datetime.now()) + ": " + " initialized DaemonSitter.")

        return

    def get_file_handler(self):
        return self.file_handler

    def send_mail(self, msg_text, subject):

        msg = MIMEMultipart()
        msg['From'] = MAIL_SENDER
        msg['To'] = ','.join(MAIL_RECEIVERS)
        msg['Subject'] = subject
        msg.attach(MIMEText(msg_text, 'plain'))

        try:
            s = smtplib.SMTP(MAIL_SERVER, 587)
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(MAIL_SERVER_UID, MAIL_SERVER_PASSWORD)
            s.sendmail(MAIL_SENDER, MAIL_RECEIVERS, msg.as_string())
            s.quit()
            self.logger.info(str(datetime.now()) + ': ' + 'emailed: ' + str(msg_text))
            return SUCCESS
        except SMTPException as e:
            self.logger.info(str(datetime.now()) + ': ' + 'sending mail failed: ' + str(e))
            return FAILURE

    def check_daemons(self):

        mail_subject = "ALERT: daemon(s) down on " + self.hostname

        for daemon in DAEMONS:
            self.logger.debug(str(datetime.now()) + ': ' + "checking on " + daemon)
            daemon_info = self.daemon_table[daemon]
            rv = call(["systemctl", "is-active", daemon])

            # daemon is running
            if rv == SYSCTL_SUCCESS:
                self.logger.debug(str(datetime.now()) + ': ' + daemon + " is active.")
                daemon_info['retry_count'] = 0
                daemon_info['notified'] = False
                daemon_info['running'] = True
            else:
                # daemon is not running
                # lets try to restart
                rc = daemon_info['retry_count']
                nf = daemon_info['notified']
                self.logger.debug(str(datetime.now()) + ': ' + daemon + " is NOT active.")
                if rc < MAX_RETRIES:
                    self.logger.debug(str(datetime.now()) + ': ' + "attempting to restart " + daemon)
                    rv = call(["systemctl", "restart", daemon])

                    # restart succeeded
                    if rv == SYSCTL_SUCCESS:
                        time.sleep(CONFIRM_INTERVAL)
                        # lets check again to see whether it is running
                        rv = call(["systemctl", "is-active", daemon])

                        # if it is still running, we are ok
                        if rv == SYSCTL_SUCCESS:
                            self.logger.debug(str(datetime.now()) + ': ' + "Restarting " + daemon + " succeeded.")
                            daemon_info['retry_count'] = 0
                            daemon_info['notified'] = False
                            daemon_info['running'] = True
                        else:
                            # it died a premature death after the restart
                            self.logger.debug(str(datetime.now()) + ': ' + "Restarted " + daemon +
                                              " failed within  " + str(CONFIRM_INTERVAL))
                            daemon_info['retry_count'] += 1
                            daemon_info['notified'] = False
                            daemon_info['running'] = False
                    else:
                        # restart failed
                        self.logger.debug(str(datetime.now()) + ': ' + "Restart attempt on " + daemon + " failed.")
                        daemon_info['retry_count'] += 1
                        daemon_info['running'] = False

                else:
                    # retry count has exceeded the set limit. but the admin has not been notified.
                    if not nf:
                        self.logger.debug(str(datetime.now()) + ': ' + "Restarting " + daemon + " failed.")
                        ec = self.send_mail("Restarting " + daemon + " failed at " +
                                            str(datetime.now()), mail_subject)
                        # at least the mailing succeeded
                        if ec == SUCCESS:
                            daemon_info['notified'] = True
                            daemon_info['running'] = False
                        # even emailing failed
                        else:
                            daemon_info['notified'] = False
                            daemon_info['running'] = False
                            self.logger.debug(str(datetime.now()) + ': ' + ' Emailing the alert message failed. ')
        return

    def send_heartbeat(self):
        current_time = datetime.now()
        td1 = current_time - self.last_message_time

        if td1.seconds < HEARTBEAT_INTERVAL:
            return
        ok_count = 0
        nok_count = 0
        ok_daemons = []
        nok_daemons = []

        for daemon in DAEMONS:
            daemon_info = self.daemon_table[daemon]

            if daemon_info['running']:
                ok_count += 1
                ok_daemons.append(daemon)
            else:
                nok_count += 1
                nok_daemons.append(daemon)

        msg_text = str(ok_count) + " daemons " + str(ok_daemons) +\
                   " are working fine and " + \
                   str(nok_count) + " " + str(nok_daemons) + " them are not."

        rv = self.send_mail("At " + str(current_time) + ":\t" + msg_text,
                            "DataGlen DaemonSitter Heartbeat from " + self.hostname + ".")
        if rv == SUCCESS:
            self.last_message_time = current_time
            self.logger.debug(str(datetime.now()) + ': ' + "Emailed heartbeat message.")
        else:
            self.logger.info(str(datetime.now()) + ': ' + "Sending heartbeat failed.")

        return

    def send_lastgasp(self):
        current_time = datetime.now()
        rv = self.send_mail("DaemonSitter is exiting at: " + str(current_time),
                            "DataGlen DaemonSitter exiting on " + self.hostname + ".")
        if rv == SUCCESS:
            self.last_message_time = current_time
            self.logger.debug(str(datetime.now()) + ': ' + "Emailed lastgasp message.")
        else:
            self.logger.info(str(datetime.now()) + ': ' + 'Sending lastgasp failed.')

        return

    def finalize(self, signum):
        self.logger.info(str(datetime.now()) + ': ' + " Received signal: " + str(signum))
        self.send_lastgasp()

    def run(self):
        while True:
            # we are sleeping first to give time to the system to settle down
            time.sleep(CHECKING_INTERVAL)
            self.check_daemons()
            self.send_heartbeat()


# Note frame argument is required for maintaining the standard signature
def handler(signum, frame):
    the_daemon_object.finalize(signum)
    sys.exit()


if __name__ == "__main__":
    the_daemon_object = ds = DaemonSitter()
    file_handler = ds.get_file_handler()
    daemon_runner = runner.DaemonRunner(ds)
    daemon_runner.daemon_context.files_preserve = [file_handler.stream]
    daemon_runner.daemon_context.signal_map = {signal.SIGTERM: handler, signal.SIGHUP: handler}
    daemon_runner.do_action()
