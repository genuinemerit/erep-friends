# coding: utf-8
#!/usr/bin/python3  # noqa: E265
"""
:module:    gm_functions
:class:     GmFunctions

Global constants and generic helper functions.

:author:    PQ <pq_rfw @ pm.me>
"""
import hashlib
import inspect
import secrets
import subprocess as shl

import arrow

from pprint import pprint as pp    # noqa: F401
from pytz import all_timezones

from gm_reference import GmReference

GR = GmReference()


class GmFunctions(object):
    """
    @class: GmFunctions

    Generic static methods.
    Functions for common tasks.
    """
    def __init__(self):
        """ Initialize GmFunctions object
        """
        pass

    def __repr__(self):
        """ Return string describing Class methods
        """
        sep = GR.LF + GR.LF + GR.LINE + GR.LF + GR.LF
        methods = "".join(
            [GR.LF + "*************************",
             GR.LF + "** GmFunctions Methods **",
             GR.LF + "*************************",
             sep,
             "get_dttm/0, get_dttm/1 -> NamedTuple " +
                GR.LF_TAB, inspect.getdoc(self.get_dttm),
             sep, "hash_me/1, hash_me/2 -> string" +
                GR.LF_TAB, inspect.getdoc(self.hash_me),
             sep, "pluralize/1 -> string" + GR.LF_TAB,
                inspect.getdoc(self.pluralize),
             sep, "run_cmd/1 -> (boolean, bytes)" + GR.LF_TAB,
                inspect.getdoc(self.run_cmd),
             sep, "exec_bash/1 -> string" + GR.LF_TAB,
                inspect.getdoc(self.exec_bash),
             sep, "get_var/1 -> (string, string)" + GR.LF_TAB,
                inspect.getdoc(self.get_var),
             sep, "get_uid/0, get_uid/1 -> string" + GR.LF_TAB,
                inspect.getdoc(self.get_uid),
             sep])
        return methods

    @classmethod
    def get_dttm(cls, p_tzone: str = None):
        """ Get date and time values.

        Args:
            p_tzone (string, optional):
                Valid Unix-style time zone. Defaults to GR.EREP_TZ.
                Examples:  America/New_York  Asia/Shanghai UTC

        Returns:
            namedtuple: GR.dttm :
            - .tz {string} Default timezone name
            - .curr_lcl {string} Default timezone date time
            - .next_lcl {string} Default date time plus 1 day
            - .curr_utc {string} UTC date time (YYYY-MM-DD HH:mm:ss.SSSSS ZZ)
            - .next_utc {string} UTC date time plus 1 day
            - .curr_ts  {string} UTC time stamp (YYYYMMDDHHmmssSSSSS)
        """
        tzone = str()
        curr_lcl = str()
        next_lcl = str()
        curr_utc = str()
        next_utc = str()
        curr_ts = str()
        p_tzone = GR.EREP_TZ if p_tzone not in all_timezones else p_tzone
        tzone = GR.EREP_TZ if p_tzone is None else p_tzone
        l_dttm = arrow.now(tzone)
        curr_lcl = str(l_dttm.format('YYYY-MM-DD HH:mm:ss.SSSSS ZZ'))
        curr_lcl_short = str(l_dttm.format('YYYY-MM-DD HH:mm:ss'))
        next_lcl =\
            str(l_dttm.shift(days=+1).format('YYYY-MM-DD HH:mm:ss.SSSSS ZZ'))
        u_dttm = arrow.utcnow()
        curr_utc = str(u_dttm.format('YYYY-MM-DD HH:mm:ss.SSSSS ZZ'))
        next_utc =\
            str(u_dttm.shift(days=+1).format('YYYY-MM-DD HH:mm:ss.SSSSS ZZ'))
        curr_ts = curr_utc.strip()
        curr_ts = curr_ts.replace(' ', '').replace(':', '').replace('-', '')
        curr_ts = curr_ts.replace('+', '').replace('.', '')
        curr_ts = curr_ts[0:-4]
        return GR.dttm(tzone,
                       curr_lcl, curr_lcl_short,
                       next_lcl, curr_utc, next_utc, curr_ts)

    @classmethod
    def hash_me(cls, p_data_in: str, p_len: int = 64):
        """ Create a hash of the input string, returning a UTF-8 hex-string.

            - 128-byte hash uses SHA512
            - 64-byte hash uses SHA256
            - 56-byte hash uses SHA224
            - 40-byte hash uses SHA1

        Args:
            p_data_in (string): data to be hashed
            p_len (integer, optional): length of hash to return.
                Default is 64.

        Returns:
            string: UTF-8-encoded hash of input argument
        """
        v_hash = str()
        v_len = GR.SHA256 if p_len is None\
            else GR.SHA256 if p_len not in GR.HASH_ALGO\
            else p_len
        if v_len == GR.SHA512:
            v_hash = hashlib.sha512()
        elif v_len == GR.SHA256:
            v_hash = hashlib.sha256()
        elif v_len == GR.SHA224:
            v_hash = hashlib.sha224()
        elif v_len == GR.SHA1:
            v_hash = hashlib.sha1()

        v_hash.update(p_data_in.encode("utf-8"))
        return v_hash.hexdigest()

    @classmethod
    def pluralize(cls, p_singular: str):
        """ Return plural form of the singular English word.

        Args:
            singular (string) English noun in singular form

        Returns:
            string: plural version of the noun
        """
        # Expand this list as needed...
        sing_is_plural = (
            'advice', 'aircraft', 'aluminum', 'barracks', 'binoculars',
            'cannon', 'cattle', 'chalk', 'clippers', 'clothing', 'concrete',
            'correspondence', 'dice', 'education', 'fish', 'food', 'furniture',
            'headquarters', 'help', 'homework', 'insignia', 'kudos', 'moose',
            'news', 'offspring', 'oxygen', 'pants', 'pyjamas', 'pliers',
            'police', 'scissors', 'series', 'shambles', 'sheep', 'shorts',
            'spacecraft', 'species', 'stuff', 'sugar', 'tongs', 'trousers',
            'you', 'wheat', 'wood')
        plural = p_singular
        if not p_singular or p_singular.strip() == ''\
                or p_singular[-2:].lower()\
                in ('es', 'ds', 'hs', 'ks', 'ms', 'ps', 'ts')\
                or p_singular.lower() in sing_is_plural:
            pass
        elif p_singular[-1:].lower() in ('s', 'x')\
                or p_singular[-2:].lower() in ('ch'):
            plural = p_singular + "es"
        elif p_singular[-1:].lower() == 'y'\
                and p_singular[-2:1].lower() not in ('a', 'e', 'i', 'o', 'u'):
            plural = p_singular[:-1] + "ies"
        else:
            plural = p_singular + "s"
        return plural

    @classmethod
    def run_cmd(cls, p_cmd: list):
        """ Execute a shell command.
            Only tested with `bash` under POSIX:Linux.
            Don't know if it will work on MacOS or Windows.

        Args:
            p_cmd (list) shell command as a string in a list

        Returns:
            tuple: (boolean success/failure, bytes result)
        """
        cmd_rc = False
        cmd_result = b''   # Stores bytes

        if p_cmd == "" or p_cmd is None:
            cmd_rc = False
        else:
            # shell=True means cmd param contains a regular cmd string
            shell = shl.Popen(p_cmd, shell=True, stdin=shl.PIPE,
                              stdout=shl.PIPE, stderr=shl.STDOUT)
            cmd_result, _ = shell.communicate()
            if 'failure'.encode('utf-8') in cmd_result\
                    or 'fatal'.encode('utf-8') in cmd_result:
                cmd_rc = False
            else:
                cmd_rc = True
        return (cmd_rc, cmd_result)

    def exec_bash(self, p_cmd_list: list):
        """ Run a series of one or more OS commands

        Args:
            p_cmd_list (list) of strings formatted correctly as OS commands

        Returns:
            string: decoded message from execution of last command in list
        """
        for cmd in p_cmd_list:
            _, result = self.run_cmd(cmd)
            result = result.decode('utf-8').strip()
        return result

    def get_var(self, p_varnm: str):
        """ Retrieve value of an environment variable.
            This method assumes POSIX type OS

        Args:
            p_varnm (string) name of environment variable

        Returns:
            tuple: (string name of requested var,
                    string value of requested var or empty string)
        """
        retval = tuple()
        (rc, rslt) = self.run_cmd("echo $" + p_varnm)
        if rc:
            retval = (p_varnm, rslt.decode('UTF-8')[0:-1])
        else:
            retval = (p_varnm, '')
        return retval

    def get_uid(self, p_uid_length: int = None):
        """ Generate a cryptographically strong random value that is URL safe.
        Unique ID for any random purpose like UID for database
        where deltas are tracked in the database.

        Args:
            p_uid_length (integer, optional): Desired length of the key.
                Default is 32. Minimum is 32.

        Returns:
            string: the unique ID value as a string
        """
        p_uid_length = 32 if p_uid_length is None else p_uid_length
        p_uid_length = 32 if p_uid_length < 32 else p_uid_length
        secret_key = secrets.token_urlsafe(p_uid_length)
        return secret_key.decode("utf-8")
