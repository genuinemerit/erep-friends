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
from collections import namedtuple
from copy import copy
from pprint import pprint as pp  # noqa: F401

import arrow
from pytz import all_timezones

from structs import Structs

ST = Structs()


class Utils(object):
    """Generic functions for common tasks."""

    @classmethod
    def get_dttm(cls, p_tzone: str) -> namedtuple:
        """Get date and time values.

        Args:
            p_tzone (string):
                Valid Unix-style time zone.
                Examples:  America/New_York  Asia/Shanghai UTC

        Returns:
            namedtuple
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
        fields = ['tz', 'curr_lcl', 'curr_lcl_short', 'next_lcl',
                  'curr_utc', 'next_utc', 'curr_ts']
        dttm = namedtuple("dttm", " ".join(fields))
        lcl_dttm = arrow.now(p_tzone)
        dttm.curr_lcl = str(lcl_dttm.format(long_format))
        dttm.curr_lcl_short = str(lcl_dttm.format(short_format))
        dttm.next_lcl = str(lcl_dttm.shift(days=+1).format(long_format))
        utc_dttm = arrow.utcnow()
        dttm.curr_utc = str(utc_dttm.format(long_format))
        dttm.next_utc = str(utc_dttm.shift(days=+1).format(long_format))
        dttm.curr_ts = dttm.curr_utc.strip()
        for rm in [' ', ':', '+', '.', '-']:
            dttm.curr_ts = dttm.curr_ts.replace(rm, '')
        dttm.curr_ts = dttm.curr_ts[0:-4]
        return dttm

    @classmethod
    def get_hash(cls,
                 p_data_in: str,
                 p_len: ST.HashLevel = ST.HashLevel.SHA256) -> str:
        """Create hash of input string, returning UTF-8 hex-string.

        - 128-byte hash uses SHA512
        - 64-byte hash uses SHA256
        - 56-byte hash uses SHA224
        - 40-byte hash uses SHA1

        Args:
            p_data_in (string): data to be hashed
            p_len (ST.HashLevel -> int, optional):
                Length of hash to return. Default is 64.

        Returns:
            string: UTF-8-encoded hash of input argument
        """
        v_hash = str()
        v_hash = hashlib.sha512() if p_len == ST.HashLevel.SHA512\
            else hashlib.sha224() if p_len == ST.HashLevel.SHA224\
            else hashlib.sha1() if p_len == ST.HashLevel.SHA1\
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
    def make_namedtuple(cls,
                        p_name: str,
                        p_dict: dict) -> namedtuple:
        """Convert dict to namedtuple.

        Args:
            p_name (str): name to assign to the tuple
            p_dict (dict): keys and value

        Returns:
            namedtuple
        """
        p_name = namedtuple(p_name, sorted(p_dict.keys()))
        return p_name(**p_dict)

    @classmethod
    def make_dict(cls,
                  p_keys: list,
                  p_tuple: namedtuple) -> dict:
        """Convert namedtuple to dict.

        Args:
            p_keys (list): names of values in tuple
            p_tuple (namedtuple)

        Returns:
            dict
        """
        data_rec = dict()
        for cnm in p_keys:
            data_rec[cnm] = copy(getattr(p_tuple, cnm))
        return data_rec

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

    def get_home(self) -> str:
        """Get name of the user's home directory

        Returns:
            str: path to $HOME
        """
        result = self.run_cmd("echo $HOME")
        home = (result[1].decode('utf8')).strip()
        return home
