# -*- coding: utf-8 -*-
#!/usr/bin/python3
"""
:module:  gm_logger
:class:   GmLogger

Generic logging class

:author:    PQ <pq_rfw @ pm.me>
"""
import inspect
import logging
# from pprint import pprint as pp
import traceback
from os import path, remove

from tornado.options import define, options

from gm_functions import GmFunctions
from gm_reference import GmReference

GF = GmFunctions()
GR = GmReference()

class GmLogger(object):
    """
    @class: GmLogger

    Generic logging functions for use with logging module.
    """
    def __init__(self, p_log_file, p_log_level=None, p_local_tz=None):
        """ Initialize the GmLogger class
            Create a new log file if one does not already exist.

        Args:
            p_log_file (path): full path to log file location
            p_log_level (string, optional): A valid log level value.
                                            Defaults to None.
            p_local_tz (string, optional): A valid Olson tz name value.
                                           Defaults to None.
        """
        self.LOGLEVEL = self.set_log_level(p_log_level)
        self.LOGFILE = p_log_file
        erep_dttm = GF.get_dttm()
        local_dttm = None
        if p_local_tz not in (None, "None", ""):
            local_dttm = GF.get_dttm(p_local_tz)
        f = open(self.LOGFILE, 'a+')
        f.write("\n== Log Session started")
        if local_dttm not in (None, "None", ""):
            f.write("\n==     Local Time: {} ({})".format(
                                    local_dttm.curr_lcl, p_local_tz))
        f.write("\n== eRepublik Time: {} ({})".format(
                                    erep_dttm.curr_lcl,GR.EREP_TZ))
        f.write("\n== Universal Time: {} ({})\n\n".format(
                                    erep_dttm.curr_utc, GR.UTC_TZ))
        f.close()

    def __repr__(self):
        """ Return string describing Class methods
            TODO Update, clean up this method after code settles down
        """
        sep = GR.LF + GR.LF + GR.LINE + GR.LF + GR.LF
        methods = "".join(
            [GR.LF  + "*************************",
             GR.LF  + "**  GmLogger Methods  **",
             GR.LF  + "*************************",
             sep, "GmLogger/1 => None" + GR.LF,
             "GmLogger/2 => None" + GR.LF_TAB, inspect.getdoc(self.__init__),
             sep, "set_log_level/0 => integer" + GR.LF,
             "set_log_level/1 => integer" + GR.LF_TAB, inspect.getdoc(self.set_log_level),
             sep, "get_log_level/1 => string" + GR.LF_TAB, inspect.getdoc(self.get_log_level),
             sep, "set_logs/0 => None" + GR.LF_TAB, inspect.getdoc(self.set_logs),
             sep, "write_log/2 => None" + GR.LF,
             "write_log/3 => None" + GR.LF_TAB, inspect.getdoc(self.write_log),
             sep, "close_logs/0 => None" + GR.LF_TAB, inspect.getdoc(self.close_logs), sep
            ])
        return methods

    def set_log_level(self, p_log_level=None):
        """ Return an integer for use by Python logging module.

        Args:
            p_log_level (string, optional): An named index to LOGLEVEL. Defaults to None.
                Examples: 'INFO', 'WARNING', 'ERROR'

        Returns:
            integer: valid value from ErepReference.LOGLEVEL
        """
        if p_log_level is None:
            return GR.LOGLEVEL['INFO']
        else:
            if p_log_level in GR.LOGLEVEL:
                return GR.LOGLEVEL[p_log_level]
            else:
                return GR.LOGLEVEL['NOTSET']

    def get_log_level(self, p_log_level_int):
        """ Return string associated with specified LOGLEVEL integer value

        Args:
            p_log_level_int (integer):  Numeric value of a valid LOGLEVEL

        Returns:
            string: index value for the ErepReference.LOGLEVEL value, or 'UNKNOWN'
            Examples: 'INFO', 'DEBUG'
        """
        for key, val in GR.LOGLEVEL.items():
            if val == p_log_level_int:
                return key
        return 'UNKNOWN'

    def set_logs(self):
        """ Set log level, log formatter and log outputs. Initiates log handling.
            Assumes that LOGLEVEL and LOGFILE have been set as desired.
        """
        self.log = logging.getLogger()
        self.log.setLevel(self.LOGLEVEL)
        # "asctime" will pull localhost timezone time.
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logF = logging.FileHandler(self.LOGFILE)
        logF.setLevel(self.LOGLEVEL)
        logF.setFormatter(formatter)
        self.log.addHandler(logF)

    def write_log(self, p_msg_level, p_msg_text, p_traceback=False):
        """ Write message at designated level
            Messages are written to console and to file.
            If requested, append a trace to the log message.

        Args:
            p_msg_level (string): Name of (i.e., key to) a LOGLEVEL
            p_msg_text (string): Content of the message to log
            p_traceback (boolean, optional): Write trace to log if True. Defaults to False.
        """
        if p_traceback:
            p_msg_text += GR.LF + repr(traceback.format_stack()) + GR.LF
        if p_msg_level not in GR.LOGLEVEL:
            ll_text = self.get_log_level(p_msg_level)
        else:
            ll_text = p_msg_level
        if ll_text in ('CRITICAL', 'FATAL'):
            logging.fatal(p_msg_text)
        elif ll_text == 'ERROR':
            logging.error(p_msg_text)
        elif ll_text == 'WARNING':
            logging.warning(p_msg_text)
        elif ll_text in ('NOTICE', 'INFO'):
            logging.info(p_msg_text)
        elif ll_text == 'DEBUG':
            logging.debug(p_msg_text)

    def close_logs(self):
        """ Close log handlers. Terminates log handling.
        """
        for handler in self.log.handlers:
            handler.close()
            self.log.removeFilter(handler)
