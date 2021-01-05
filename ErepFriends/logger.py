# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Generic logging class.

Module:  logger
Class:   Logger
Author:    PQ <pq_rfw @ pm.me>
"""
import logging
import traceback
from pprint import pprint as pp  # noqa: F401

from structs import Structs
from utils import Utils

UT = Utils()
ST = Structs()


class Logger(object):
    """Generic logging functions for use with logging module."""

    def __init__(self,
                 p_log_file: str,
                 p_log_level: ST.LogLevel = ST.LogLevel.NOTSET,
                 p_local_tz: str = None):
        """Initialize the Logger class.

        Create a new log file if one does not already exist.

        Args:
            p_log_file (path): full path to log file location
            p_log_level (ST.LogLevel -> int, optional):
                A valid log level value. Defaults to NOTSET (= 0).
            p_local_tz (string, optional): A valid Olson tz name value.
                                           Defaults to None.
        """
        self.LOGLEVEL = p_log_level
        self.LOGFILE = p_log_file
        erep_dttm = UT.get_dttm(ST.TimeZone.EREP)
        local_dttm = None
        local_dttm = UT.get_dttm(p_local_tz)\
            if p_local_tz not in (None, "None", "")\
            else UT.get_dttm(p_local_tz)
        f = open(self.LOGFILE, 'a+')
        f.write("\n== Log Session started")
        f.write("\n==     Local Time: {} ({})".format(
                local_dttm.curr_lcl, p_local_tz))
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
                  p_msg_text: str,
                  p_traceback: bool = False):
        """Write message at designated level.

        Messages are written to console and to file.
        If requested, append a trace to the log message.

        Args:
            p_msg_level (ST.LogLevel -> int): Valid log level value
            p_msg_text (string): Content of the message to log
            p_traceback (bool, optional): Write trace to log if True.
                                          Defaults to False.
        """
        if p_traceback:
            p_msg_text += ST.TextHelp.LF +\
                          repr(traceback.format_stack()) + ST.TextHelp.LF
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
