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
    """Constants, data structures."""

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

    @dataclass
    class MsgLevel:
        """Define supported tkinter messagebox types."""

        INFO: str = 'INFO'
        WARN: str = 'WARN'
        ERROR: str = 'ERROR'

        def keys():
            """Get column names."""
            return list(Structs.MsgLevel.__dataclass_fields__.keys())

# DATA STRUCTURES. Database Schema.

    @dataclass
    class AuditFields:
        """Define audit columns used on all tables."""

        uid: str = None
        hash_id: str = None
        pid: str = None
        create_ts: str = None
        update_ts: str = None
        delete_ts: str = None

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

        def keys():
            """Get column names."""
            return list(Structs.ConfigFields.__dataclass_fields__.keys())

    @dataclass
    class TextFields:
        """Define static text items."""

        app_ttl: str = 'Analyze eRepublik Citizens Data'
        cfg_ttl: str = 'Configure ErepFriends'
        collect_ttl: str = 'Collect Citizen Data'
        m_file: str = 'File'
        m_save: str = 'Save'
        m_close: str = 'Close'
        m_quit: str = 'Exit'
        m_win: str = 'Windows'
        m_cfg: str = 'Configure ErepFriends'
        m_collect: str = 'Collect Citizen Data'
        m_help: str = 'Help'
        m_docs: str = 'User Guide'
        m_about: str = 'About'
        m_cfg_lbl: str = 'Enter configuration choices,' +\
                         'then select File-->Save'
        m_logs: str = 'Log location'
        m_log_level: str = 'Log level'
        m_bkups: str = 'Backup DBs location'
        m_bkups_btn: str = 'Set backups path'
        m_email: str = 'eRep Email Login'
        m_passw: str = 'eRep Password'
        m_apikey: str = 'eRep Tools API Key'
        m_getfriends: str = 'Refresh user friends list:'
        m_getfriends_btn: str = 'Post request to eRepublik'
        m_getcit_byid: str = 'Get citizen data by ID:'
        m_getcit_byid_btn: str = 'Get citizen profile'
        m_getcit_bynm: str = 'Get citizen data by Name:'
        m_getcit_bynm_btn: str = 'Get citizen profile'
        m_connect_lbl: str = 'Press button to verify credentials.' +\
                             ' Then press button to refresh user profile.'
        m_creds: str = 'Verify eRep credentials: '
        m_creds_btn: str = 'Post eRep Login'
        m_profile: str = 'Refresh eRep profile data: '
        m_profile_btn: str = 'Get Data'
        m_idf_loc: str = 'Read Profile IDs from file:'
        m_idf_loc_set_btn: str = 'Set File'
        m_idf_loc_get_btn: str = 'Refresh citizen profiles'
        m_db_refresh: str = 'Refresh all on Database'
        m_db_refresh_btn: str = 'Get profile data'
        b_pick_file: str = "Select a file"
        b_set_log_path: str = "Set Log Path"
        b_set_dbkup_path: str = "Set backups path"
        b_save_log_btn: str = "Update log config"
        b_save_bkups_btn: str = "Update backups config"
        b_save_creds_btn: str = "Verify/Update eRep login"
        b_save_apikey_btn: str = "Verify/Update API key"
        m_info_ttl: str = "Information"
        m_warn_ttl: str = "Warning"
        m_error_ttl: str = "Error"
        m_log_data: str = "Log information updated."
        m_logging_on: str = "Loggging turned on."
        m_bkup_data: str = "DB backup data updated."
        m_bkups_on: str = "Backup and Archive databases enabled."
        m_user: str = "User verified."
        m_user_key: str = "Tried using the API key."
        m_user_data: str = "User credentials and profile stored."
        m_user_key_ok: str = "User eRep Tools API key verified."
        m_user_key_not_ok: str = "User eRep Tools API key FAILED verification."
        connected: str = 'Login to eRepublik verified'
        login_failed: str = 'eRep login failed. Please review credentials'
        greet: str = 'Greetings, [user]!'

        def keys():
            """Get column names."""
            return list(Structs.TextFields.__dataclass_fields__.keys())

    @dataclass
    class UserFields:
        """Define non-audit columns on user table."""

        user_erep_profile_id: str = None
        user_erep_email: str = None
        user_erep_password: str = None
        user_tools_api_key: str = None
        encrypt_key: str = None

        def keys():
            """Get column names."""
            return list(Structs.UserFields.__dataclass_fields__.keys())

    @dataclass
    class CitizenFields:
        """Define non-audit columns on citizens table."""

        profile_id: str = None
        name: str = None
        is_user_friend: str = None
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
            return list(Structs.CitizenFields.__dataclass_fields__.keys())
