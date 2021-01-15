# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Global constants and data structures.

Module:  structs
Class:   Structs
Author:    PQ <pq_rfw @ pm.me>
"""
from dataclasses import dataclass
from pprint import pprint as pp  # noqa: F401


class Structs(object):
    """Codes, constants, types, structures.

    - Reference codes and constants
    - Non-standard datatypes
    - Data structures
    """

# CONSTANTS

    @dataclass
    class TimeZone:
        """Define commonly-used time zone values."""

        EREP: str = 'America/Los_Angeles'
        UTC: str = 'UTC'

    @dataclass
    class TextHelp:
        """Define useful constants for displaying text."""

        LF: str = '\n'
        LF_TAB: str = '\n\t'
        LF_TABx2: str = '\n\t\t'
        TAB: str = '\t'
        TABx2: str = '\t\t'
        LINE: str = '======================================='

    @dataclass
    class LogLevel:
        """Define valid logging levels."""

        CRITICAL: int = 50
        FATAL: int = 50
        ERROR: int = 40
        WARNING: int = 30
        NOTICE: int = 20
        INFO: int = 20
        DEBUG: int = 10
        NOTSET: int = 0

        def keys():
            """Get column names."""
            return list(Structs.LogLevel.__dataclass_fields__.keys())

    @dataclass
    class HashLevel:
        """Define valid hashing levels."""

        SHA512: int = 128
        SHA256: int = 64
        SHA224: int = 56
        SHA1: int = 40

        def keys():
            """Get column names."""
            return list(Structs.HashLevel.__dataclass_fields__.keys())

# DATA STRUCTURES -- Database tables

    @dataclass
    class AuditFields:
        """Define audit columns used on all tables."""

        uid: str = None
        pid: str = None
        hash_id: str = None
        create_ts: str = None
        update_ts: str = None
        delete_ts: str = None
        is_encrypted: str = None

        def keys():
            """Get column names."""
            return list(Structs.AuditFields.__dataclass_fields__.keys())

    @dataclass
    class ConfigFields:
        """Define configuration items."""

        erep_url: str = 'https://www.erepublik.com/en'

        log_name: str = 'efriends.log'
        log_path: str = None
        log_level: str = None

        db_dir_path: str = './db'
        db_name: str = 'efriends.db'
        main_db_path: str = None
        main_db: str = None
        bkup_db_path: str = None
        bkup_db: str = None
        arcv_db_path: str = None
        arcv_db: str = None

        w_app_ttl: str = 'eRepublik Friends Analysis'
        w_cfg_ttl: str = 'eRepublik Friends Configuration'
        w_m_file: str = 'File'
        w_m_save: str = 'Save'
        w_m_close: str = 'Close'
        w_m_quit: str = 'Exit'
        w_m_win: str = 'Windows'
        w_m_cfg: str = 'Configure'
        w_m_help: str = 'Help'
        w_m_docs: str = 'User Guide'
        w_m_about: str = 'About'

        w_m_cfg_lbl: str = 'Enter configuration choices,' +\
                           'then select File-->Save'
        w_m_logs: str = 'Log location'
        w_m_log_level: str = 'INFO'
        w_m_bkups: str = 'Backup DBs location'
        w_m_email: str = 'eRep Email Login'
        w_m_passw: str = 'eRep Password'

        w_b_pick_file: str = "Select a file"
        w_b_set_log_path: str = "Set Log Path"
        w_b_set_dbkup_path: str = "Set DB Backup Path"

        w_connected: str = 'Login to eRepublik verified'
        w_login_failed: str = 'eRep login failed. Please review credentials'
        w_greet: str = 'Welcome, [user]!'

        def keys():
            """Get column names."""
            return list(Structs.ConfigFields.__dataclass_fields__.keys())

    @dataclass
    class UserFields:
        """Define non-audit columns on user table."""

        user_erep_profile_id: str = None
        user_erep_email: str = None
        user_erep_password: str = None
        encrypt_all: str = None
        encrypt_key: str = None

        def keys():
            """Get column names."""
            return list(Structs.UserFields.__dataclass_fields__.keys())

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

        def keys():
            """Get column names."""
            return list(Structs.FriendsFields.__dataclass_fields__.keys())
