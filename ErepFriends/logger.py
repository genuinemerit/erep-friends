# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Generic logging class.

Module:  logger
Class:   Logger
Author:    PQ <pq_rfw @ pm.me>
"""
import logging
from copy import copy
from pprint import pprint as pp  # noqa: F401

from tzlocal import get_localzone

from structs import Structs
from utils import Utils

UT = Utils()
ST = Structs()


class Logger(object):
    """Generic logging functions for use with logging module."""

    def __init__(self,
                 p_log_file: str,
                 p_log_level: ST.LogLevel = ST.LogLevel.NOTSET):
        """Initialize the Logger class.

        Create a new log file if one does not already exist.

        Args:
            p_log_file (path): full path to log file location
            p_log_level (ST.LogLevel -> int, optional):
                A valid log level value. Defaults to NOTSET (= 0).
        """
        self.LOGLEVEL = p_log_level
        self.LOGFILE = p_log_file
        erep_dttm = copy(UT.get_dttm(ST.TimeZone.EREP))
        localhost_tz = get_localzone()
        localhost_dttm = copy(UT.get_dttm(localhost_tz.zone))
        f = open(self.LOGFILE, 'a+')
        f.write("\n== Log Session started")
        f.write("\n== Localhost Time: {} ({})".format(
                localhost_dttm.curr_lcl, localhost_tz))
        f.write("\n== eRepublik Time: {} ({})".format(
                erep_dttm.curr_lcl, ST.TimeZone.EREP))
        f.write("\n== Universal Time: {} ({})\n\n".format(
                erep_dttm.curr_utc, ST.TimeZone.UTC))
        f.close()

    def set_log(self):
        """Set log level, log formatter and log outputs. Initiates log handling.

        Assumes that LOGLEVEL and LOGFILE have been set correctly.
        """
        self.log = logging.getLogger()
        self.log.setLevel(self.LOGLEVEL)
        # "asctime" will pull the actual localhost timezone time.
        msg_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(msg_format)
        logF = logging.FileHandler(self.LOGFILE)
        logF.setLevel(self.LOGLEVEL)
        logF.setFormatter(formatter)
        self.log.addHandler(logF)

    def write_log(self,
                  p_msg_level: ST.LogLevel,
                  p_msg_text: str):
        """Write message at designated level.

        Args:
            p_msg_level (ST.LogLevel -> int): Valid log level value
            p_msg_text (string): Content of the message to log
        """
        if p_msg_level in (ST.LogLevel.CRITICAL, ST.LogLevel.FATAL):
            logging.fatal(p_msg_text)
        elif p_msg_level == ST.LogLevel.ERROR:
            logging.error(p_msg_text)
        elif p_msg_level == ST.LogLevel.WARNING:
            logging.warning(p_msg_text)
        elif p_msg_level in (ST.LogLevel.NOTICE, ST.LogLevel.INFO):
            logging.info(p_msg_text)
        elif p_msg_level == ST.LogLevel.DEBUG:
            logging.debug(p_msg_text)

    def close_log(self):
        """Close log handlers. Terminate log handling."""
        for handler in self.log.handlers:
            handler.close()
            self.log.removeFilter(handler)
