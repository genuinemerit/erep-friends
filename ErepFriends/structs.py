# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Global constants and data structures.

Module:  structs
Class:   Structs
Sub-classes:
    UserRecord
    FriendsRecord
Author:    PQ <pq_rfw @ pm.me>
"""
from dataclasses import dataclass
from pprint import pprint as pp  # noqa: F401
from typing import Literal, NamedTuple


class Structs(object):
    """Codes, constants, types, structures.

    @class: Structs

    - Standard reference codes and constants:
      - Severity levels
      - Hash lengths and codes
      - Default time zone
      - Values for tabs and newlines
    - Standard types
    - Standard structures
    """

    def __init__(self):
        """Initialize the object."""
        self.DBSCHEMA = {
            'user':
                {'data': self.UserFields(), 'audit': self.AuditFields()},
            'friends':
                {'data': self.FriendsFields(), 'audit': self.AuditFields()}}

    @dataclass
    class LOGLEVEL:
        """Define valid logging levels."""

        CRITICAL: int = 50
        FATAL: int = 50
        ERROR: int = 40
        WARNING: int = 30
        NOTICE: int = 20
        INFO: int = 20
        DEBUG: int = 10
        NOTSET: int = 0
        t_values = Literal[0, 10, 20, 30, 40, 50]
        t_names = Literal['NOTSET', 'DEBUG', 'INFO', 'NOTICE',
                          'WARNING', 'ERROR', 'FATAL', 'CRITICAL']

    @dataclass
    class HASH:
        """Define valid hashing levels."""

        SHA512: int = 128
        SHA256: int = 64
        SHA224: int = 56
        SHA1: int = 40
        t_values = Literal[40, 56, 64, 128]
        t_names = Literal['SHA1', 'SHA224', 'SHA256', 'SHA512']

    @dataclass
    class TIMEZONE:
        """Define commonly-used time zone values."""

        EREP: str = 'America/Los_Angeles'
        UTC: str = 'UTC'

    @dataclass
    class TXT:
        """Define some useful constants for displaying text."""

        LF: str = '\n'
        LF_TAB: str = '\n\t'
        LF_TABx2: str = '\n\t\t'
        TAB: str = '\t'
        TABx2: str = '\t\t'
        LINE: str = '======================================='

    class Types(object):
        """Define non-standard data types."""

        t_dbaction = Literal['add', 'upd', 'del']
        t_tblnames = Literal['user', 'friends']
        t_ffilters = Literal['uid', 'name', 'profile_id', 'party_name',
                             'militia_name', 'level', 'xp']
        t_namedtuple = NamedTuple

    @dataclass
    class DateTime:
        """Define date-time fields supported by the system."""

        tz: str = None
        curr_lcl: str = None
        curr_lcl_short: str = None
        next_lcl: str = None
        curr_utc: str = None
        next_utc: str = None
        curr_ts: str = None

    @dataclass
    class ConfigFields:
        """Define values used in configuration file."""

        cfg_file_name: str = "efriends.conf"
        db_name: str = 'efriends.db'
        data_path: str = './db'
        bkup_db_path: str = None
        arcv_db_path: str = None
        log_path: str = None
        log_level: str = 'INFO'
        log_name: str = 'efriends.log'
        local_tz: str = None
        erep_url: str = 'https://www.erepublik.com/en'
        w_txt_title: str = "eRepublik Friends Analysis"
        w_txt_greet: str = "Welcome, [user]!"
        w_txt_connected: str = "You are now logged in to eRepublik"
        w_txt_disconnected: str = "You are now logged out of eRepublik"
        w_txt_login_failed: str =\
            "eRep login failed. Please check credentials"

    @dataclass
    class AuditFields:
        """Define audit columns used on all tables."""

        uid: str = None
        encrypt_all: str = None
        hash_id: str = None
        create_ts: str = None
        update_tsdelete_ts: str = None
        is_encrypted: str = None
        fields = [col_nm for col_nm in self.__dict__
                    if not callable(getattr(self, col_nm))
                     and col_nm[:2] != "__"]

    @dataclass
    class UserFields:
        """Define non-audit columns on user table."""

        user_erep_profile_id: str = None
        user_erep_email: str = None
        user_erep_password: str = None
        encrypt_all: str = None
        encrypt_key: str = None
        fields = [col_nm for col_nm in self.__dict__
                    if not callable(getattr(self, col_nm))
                     and col_nm[:2] != "__"]

    @dataclass
    class FriendsFields:
        """Define non-audit columns on friends table."""

        profile_id: str = None
        name: str = None
        is_alive: str = None
        is_adult: str = None
        avatar_link: str = None
        level: str = None
        xp: str = None
        friends_count: str = None
        achievements_count: str = None
        citizenship_country: str = None
        residence_city: str = None
        residence_region: str = None
        residence_country: str = None
        is_in_congress: str = None
        is_ambassador: str = None
        is_dictator: str = None
        is_country_president: str = None
        is_top_player: str = None
        is_party_member: str = None
        is_party_president: str = None
        party_name: str = None
        party_avatar_link: str = None
        party_orientation: str = None
        party_url: str = None
        militia_name: str = None
        militia_url: str = None
        militia_size: str = None
        militia_avatar_link: str = None
        military_rank: str = None
        aircraft_rank: str = None
        ground_rank: str = None
        newspaper_name: str = None
        newspaper_avatar_link: str = None
        newspaper_url: str = None
        fields = [col_nm for col_nm in self.__dict__
                    if not callable(getattr(self, col_nm))
                     and col_nm[:2] != "__"]
