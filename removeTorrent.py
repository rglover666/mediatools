#!/usr/bin/env python
import os
import sys
import json
import urllib
import struct
import logging
import transmissionrpc
import tvdb_api
from tvdb_api import tvdb_error
import smtplib
import configparser
import datetime
from socket import gethostbyname
from dateutil import tz
from logging.config import fileConfig
from email.mime.text import MIMEText

try:
    configPath = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), 'removeTorrent.ini')).replace("\\", "\\\\")
    Config = configparser.ConfigParser(inline_comment_prefixes=(';','#'))
    Config.read(configPath)
    logpath = Config.get('logging', 'path')

    if os.name == 'nt':
        logpath = os.path.dirname(sys.argv[0])
    elif not os.path.isdir(logpath):
        try:
            os.mkdir(logpath)
        except:
            logpath = os.path.dirname(sys.argv[0])

    loggerConfigPath = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), 'logging.ini')).replace("\\", "\\\\")
    logPath = os.path.abspath(os.path.join(logpath, Config.get('logging', 'filename'))).replace("\\", "\\\\")
    fileConfig(loggerConfigPath, defaults={'logfilename': logPath})
    log = logging.getLogger("SickChillPostConversion")
except Exception as e:
    print("Error initializing logger: {}".format(getattr(e, 'message', repr(e))))
    sys.exit()

log.info("SickChill extra script post processing started.")

if len(sys.argv) > 4:
    inputfile = sys.argv[1]
    original = sys.argv[2]
    tvdb_id = int(sys.argv[3])
    seasonNum = int(sys.argv[4])
    episodeNum = int(sys.argv[5])

    log.info("Input file: %s." % inputfile)
    log.info("Original name: %s." % original)
    log.info("TVDB ID: %s." % tvdb_id)
    log.info("Season: %s episode: %s." % (seasonNum, episodeNum))

    try:
        t = tvdb_api.Tvdb(apikey="827a143066a6d3770c13a04295e04eb5")
        series = t[tvdb_id]
        log.info("Found series.")
        episode = t[tvdb_id][seasonNum][episodeNum]
        log.info("Found episode.")
        mail_user = Config.get('email', 'user')
        mail_password = Config.get('email', 'password')

        sent_from = Config.get('email', 'sent_from')
        to = Config.get('email', 'to')
        now = datetime.datetime.now(tz = tz.tzlocal())
        date = now.strftime("%d %b %Y %H:%M:%S %Z")
        subject = "Show Downloaded: {} - S{:02d}E{:02d}".format(series['seriesName'], seasonNum, episodeNum)
        log.info("Email subject successfully constructed.")
        body = "Episode Name: %s\n\nOverwiew: %s" % (episode['episodeName'], episode['overview'])
        log.info("Email body successfully constructed.")

        email_text = """\
From: %s
To: %s
Date: %s
Subject: %s

%s
""" % (sent_from, to, date, subject, body)

        msg = MIMEText(body.encode('utf-8'), _charset='utf-8')
        msg['From'] = sent_from
        msg['To'] = to
        msg['Date'] = date
        msg['Subject'] = subject

        log.info("Email message successfully constructed.")
        try:
            smtp = Config.get('email', 'smtp_server')
            port = Config.get('email', 'smtp_port')
            server = smtplib.SMTP(smtp, port)
            log.info("Successfully retrieved email server.")
            server.ehlo()
            log.info("Successfully sent ehlo to email server.")
            server.starttls()
            log.info("Successfully sent starttls to email server.")
            server.login(mail_user, mail_password)
            log.info("Successfully logged in to email server.")
            server.sendmail(sent_from, to, msg.as_string())
            log.info("Email successfully sent.")
            server.quit()
            log.info("Successfully closed email server.")
        except SMTPAuthenticationError as a:
            log.error("Authentication error: {}".format(getattr(a, 'message', repr(a))))
        except SMTPRecipientsRefused as r:
            log.error("Recipients refused: {}".format(getattr(r, 'message', repr(r))))
        except SMTPSenderRefused as s:
            log.error("Sender refused: {}".format(getattr(s, 'message', repr(s))))
        except Exception as e:
            log.error("Error sending email: {}".format(getattr(e, 'message', repr(e))))
        
    except tvdb_error as t:
        log.error("Error communicating with thetvdb: {}".format(getattr(t, 'message', repr(t))))
    except Exception as e:
        log.error("Error processing email: {}".format(getattr(e, 'message', repr(e))))

    try:
        log.info("Connecting to Transmission RPC")
        host = Config.get('transmission', 'host')
        port = Config.get('transmission', 'port')
        tc = transmissionrpc.Client(gethostbyname('transmission.domain.com'), port)
        torrents = tc.get_torrents()
        log.info("Retrieved list of %s torrents" % len(torrents))
        log.info("Looking for torrent %s"  % original)
        found = False
        for index in range(len(torrents)):
            log.info("Found torrent %s"  % torrents[index].name)
            if torrents[index].name in original:
                found = True
                if torrents[index].isFinished == True:
                    log.info("Removing torrent: %s." % original)
                    tc.remove_torrent(torrents[index].id, True)
                else:
                    log.info("Torrent %s is not finished." % original)
                break

        if found is False:
            log.info("Torrent %s not found." % original)
    except Exception as e:
        log.error("Error removing torrent: {}".format(getattr(e, 'message', repr(e))))
else:
    log.error("Not enough command line arguments present %s." % len(sys.argv))

sys.exit()
