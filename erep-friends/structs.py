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
        oid: str = None
        create_ts: str = None
        update_ts: str = None
        delete_ts: str = None

        def keys():
            """Get column names."""
            return list(Structs.AuditFields.__dataclass_fields__.keys())

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
