# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Global constants and generic helper functions.

Module:    utils
Class:     Utils
Author:    PQ <pq_rfw @ pm.me>
"""
import hashlib
import secrets
import subprocess as shl
from pprint import pprint as pp  # noqa: F401

import arrow
from pytz import all_timezones

from structs import Structs

ST = Structs()


class Utils(object):
    """Generic functions for common tasks."""

    @classmethod
    def get_dttm(cls, p_tzone: str = None) -> ST.DateTime:
        """Get date and time values.

        Args:
            p_tzone (string, optional):
                Valid Unix-style time zone. Defaults to ST.TIMEZONE.EREP_TZ.
                Examples:  America/New_York  Asia/Shanghai UTC

        Returns:
            object: ST.DateTime
            - .tz {string} Default timezone name
            - .curr_lcl {string} Default tz date time w/seconds and zone
            - .curr_lcl_short {string} Default date time w/o secs and zone
            - .next_lcl {string} Default date time plus 1 day
            - .curr_utc {string} UTC date time (YYYY-MM-DD HH:mm:ss.SSSSS ZZ)
            - .next_utc {string} UTC date time plus 1 day
            - .curr_ts  {string} UTC time stamp (YYYYMMDDHHmmssSSSSS)
        """
        long_format = 'YYYY-MM-DD HH:mm:ss.SSSSS ZZ'
        short_format = 'YYYY-MM-DD HH:mm:ss'
        ST.DateTime.tzone = ST.TIMEZONE.EREP\
            if (p_tzone not in all_timezones or p_tzone is None)\
            else p_tzone
        lcl_dttm = arrow.now(ST.DateTime.tzone)
        ST.DateTime.curr_lcl = str(lcl_dttm.format(long_format))
        ST.DateTime.curr_lcl_short = str(lcl_dttm.format(short_format))
        ST.DateTime.next_lcl =\
            str(lcl_dttm.shift(days=+1).format(long_format))
        utc_dttm = arrow.utcnow()
        ST.DateTime.curr_utc = str(utc_dttm.format(long_format))
        ST.DateTime.next_utc =\
            str(utc_dttm.shift(days=+1).format(long_format))
        ST.DateTime.curr_ts = ST.DateTime.curr_utc.strip()
        for rm in [' ', ':', '+', '.', '-']:
            ST.DateTime.curr_ts = ST.DateTime.curr_ts.replace(rm, '')
        ST.DateTime.curr_ts = ST.DateTime.curr_ts[0:-4]
        return ST.DateTime

    @classmethod
    def get_hash(cls,
                 p_data_in: str,
                 p_len: ST.HASHALGO.t_values = 64) -> str:
        """Create hash of input string, returning UTF-8 hex-string.

        - 128-byte hash uses SHA512
        - 64-byte hash uses SHA256
        - 56-byte hash uses SHA224
        - 40-byte hash uses SHA1

        Args:
            p_data_in (string): data to be hashed
            p_len (ST.HASHALGO.t_values -> integer, optional):
                Length of hash to return. Default is 64.

        Returns:
            string: UTF-8-encoded hash of input argument

        if v_len == ST.HASH.SHA512:
            v_hash = hashlib.sha512()
        elif v_len == ST.HASH.SHA256:
            v_hash = hashlib.sha256()
        elif v_len == ST.HASH.SHA224:
            v_hash = hashlib.sha224()
        elif v_len == ST.HASH.SHA1:
            v_hash = hashlib.sha1()
        """
        v_hash = str()
        v_hash = hashlib.sha512() if p_len == ST.HASH.SHA512\
            else hashlib.sha224() if p_len == ST.HASH.SHA224\
            else hashlib.sha1() if p_len == ST.HASH.SHA1\
            else hashlib.sha256()
        v_hash.update(p_data_in.encode("utf-8"))
        return v_hash.hexdigest()

    @classmethod
    def pluralize(cls, p_singular: str) -> str:
        """Return plural form of a singular-form English noun.

        Args:
            p_singular (string) English noun in singular form

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
    def run_cmd(cls, p_cmd: list) -> tuple:
        """Execute a shell command.

        Only tested with `bash` shell under POSIX:Linux.
        Don't know if it will work properly on MacOS or Windows
        or with other shells.

        Args:
            p_cmd (list) shell command as a string in a list

        Returns:
            tuple: (success/failure: bool, result: bytes)
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

    def exec_bash(self, p_cmd_list: list) -> str:
        """Run a series of one or more OS commands.

        Args:
            p_cmd_list (list) of strings formatted correctly as OS commands
            for use in call to run_cmd/1

        Returns:
            string: decoded message from execution of last command in list
        """
        for cmd in p_cmd_list:
            _, result = self.run_cmd(cmd)
            result = result.decode('utf-8').strip()
        return result

    def get_uid(self, p_uid_length: int = None) -> str:
        """Generate a  URL safe cryptographically strong random value.

        Not a hash.  Just a unique identifier for any purpose, such as
        unique PK for a database.

        Args:
            p_uid_length (integer, optional): Desired length of the key.
                Default is 32. Minimum is 32.

        Returns:
            string: the unique ID value as a string
        """
        p_uid_length = 32 if p_uid_length is None else p_uid_length
        p_uid_length = 32 if p_uid_length < 32 else p_uid_length
        uid_val = secrets.token_urlsafe(p_uid_length)
        return uid_val
