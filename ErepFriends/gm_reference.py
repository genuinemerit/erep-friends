# coding: utf-8
#!/usr/bin/python3  # noqa: E265

"""
:module:  gm_reference
:class:   GmReference

Global constants.

:author:    PQ <pq_rfw @ pm.me>
"""

from collections import namedtuple
from pprint import pprint as pp      # noqa: F401
from pytz import all_timezones
from typing import Any, Collection, Literal, NamedTuple, NewType, NoReturn, Optional, OrderedDict, Union   # noqa: E501, F401


class GmReference(object):

    """
    Codes, constants, types, structures.

    @class: GmReference

    - Standard reference codes and constants:
      - Severity levels
      - Hash lengths and codes
      - Default time zone
      - Values for tabs and newlines
    - Standard types
    - Standard structures
    """

    def __init__(self):
        self.__set_values()
        self.__set_types()
        self.__set_structures()

    def __repr__(self):
        """ Return description of Class
            TODO
                Update after code settles down again.
        """
        sep = self.LF + self.LF + self.LINE + self.LF + self.LF
        values = "".join([
          self.LF + "*************************",
          self.LF + "** GmReference Values  **",
          self.LF + "*************************",
          sep, "LOGLEVEL:", self.TAB, str(self.LOGLEVEL),
          sep, "SHA512:", self.TABx2, str(self.SHA512),
          self.LF, "SHA256:", self.TABx2, str(self.SHA256),
          self.LF, "SHA224:", self.TABx2, str(self.SHA224),
          self.LF, "SHA1:", self.TABx2, str(self.SHA1),
          sep, "DFLT_TZ:", self.TAB, self.DFLT_TZ,
          sep, "LF:", self.TABx2, "\\n",
          self.LF, "LF_TAB:", self.TABx2, "\\n\\t",
          self.LF, "LF_TABx2:", self.TAB, "\\n\\t\\t",
          self.LF, "TAB:", self.TABx2, "\\t",
          self.LF, "TABx2:", self.TABx2, "\\t\\t",
          self.LF, "LINE:", self.TABx2, self.LINE,
          sep, "NOT_DELETED:", self.TAB, self.NOT_DELETED,
          sep, "DBACTION", self.TAB, self.DBACTION,
          sep, "DBTABLE", self.TAB, self.DBTABLE,
          sep, "FRIEND_FILTER", self.TAB, self.FRIEND_FILTER,
          sep])
        types = "".join([
          self.LF + "*************************",
          self.LF + "** GmReference Types  **",
          self.LF + "*************************",
          sep + "dbaction_t", self.TAB, "Literal{}".format(str(self.DBACTION)),
          sep + "dbtable_t", self.TAB, "Literal{}".format(str(self.DBTABLE)),
          sep + "filter_t", self.TAB, "Literal{}".format(str(self.FRIEND_FILTER)),
          sep + "NamedTuple",
          sep + "NoReturn",
          sep])
        structs = "".join([
          self.LF + "*************************",
          self.LF + "** GmReference Structs **",
          self.LF + "*************************",
          sep + "(dttm. {})".format(str(self.dttm._fields)),
          sep + "(friends_rec. {})".format(str(self.friends_rec._fields)),
          sep + "(user_rec. {})".format(str(self.encrypt_rec._fields)),
          sep])
        return values + types + structs

    def __set_values(self):
        """ Set constant values
        """
        self.LOGLEVEL = {'CRITICAL': 50,
                         'FATAL': 50,
                         'ERROR': 40,
                         'WARNING': 30,
                         'NOTICE': 20,
                         'INFO': 20,
                         'DEBUG': 10,
                         'NOTSET': 0}
        self.SHA512 = 128
        self.SHA256 = 64
        self.SHA224 = 56
        self.SHA1 = 40
        self.HASH_ALGO = {
            40: 'SHA1', 56: 'SHA224', 64: 'SHA256', 128: 'SHA512'}
        self.EREP_TZ = 'America/Los_Angeles'
        self.UTC_TZ = 'UTC'
        self.LF = '\n'
        self.LF_TAB = '\n\t'
        self.LF_TABx2 = '\n\t\t'
        self.TAB = '\t'
        self.TABx2 = '\t\t'
        self.LINE = '======================================='
        self.NOT_DELETED = '9999-99-99 99:99:99.99999 +00:00'
        self.DBACTION = ['add', 'upd', 'del']
        self.DBTABLE = ['user', 'friends']
        self.FRIEND_FILTER = ['uid', 'name', 'profile_id', 'party_name',
                              'militia_name', 'level', 'xp']

    def __set_types(self):
        """ Set types
        """
        self.dbaction_t = Literal['add', 'upd', 'del']
        self.dbtable_t = Literal['user', 'friends']
        self.filter_t = Literal['uid', 'name', 'profile_id', 'party_name',
                              'militia_name', 'level', 'xp']
        self.NamedTuple = NamedTuple
        self.NoReturn = NoReturn

    def __set_structures(self):
        """ Set data structures
        """
        # INTERNAL DATA STRUCTURES
        # dttm named tuple
        fields =\
            'tz curr_lcl curr_lcl_short next_lcl curr_utc next_utc curr_ts'
        self.dttm = namedtuple('dttm', fields)

        # CONFIGURATION FILE
        self.configs = {
            "cfg_file_name": "efriends.conf",
            "db_name": 'efriends.db',
            "data_path": './db',
            "bkup_db_path": None,
            "arcv_db_path": None,
            "log_path": None,
            "log_level": 'INFO',
            "log_name": 'efriends.log',
            "local_tz": None,
            "erep_url": 'https://www.erepublik.com/en',
            "w_txt_title": "eRepublik Friends Analysis",
            "w_txt_greet": "Welcome, [user]!",
            "w_txt_connected": "You are now logged in to eRepublik",
            "w_txt_disconnected": "You are now logged out of eRepublik",
            "w_txt_login_failed": "eRep login failed. Please check credentials"}

        # DATABASE TABLES
        # user_rec
        fields = " ".join(['uid',
                           'user_erep_profile_id',
                           'user_erep_email',
                           'user_erep_password',
                           'encrypt_all',
                           'encrypt_key',
                           'hash_id', 'create_ts', 'update_ts', 'delete_ts',
                           'is_encrypted'])
        self.user_rec = namedtuple('user_rec', fields)
        # friends_rec
        fields = " ".join(['uid',
                           'profile_id', 'name',
                           'is_alive', 'is_adult', 'avatar_link',
                           'level', 'xp', 'friends_count',
                           'achievements_count', 'citizenship_country',
                           'residence_city', 'residence_region',
                           'residence_country', 'is_in_congress',
                           'is_ambassador', 'is_dictator',
                           'is_country_president', 'is_top_player',
                           'is_party_member', 'is_party_president',
                           'party_name', 'party_avatar_link',
                           'party_orientation', 'party_url',
                           'militia_name', 'militia_url',
                           'militia_size', 'militia_avatar_link',
                           'military_rank', 'aircraft_rank',
                           'ground_rank', 'newspaper_name',
                           'newspaper_avatar_link', 'newspaper_url',
                           'hash_id', 'create_ts', 'update_ts', 'delete_ts',
                           'is_encrypted'])
        self.friends_rec = namedtuple('friends_rec', fields)
        # auto_fields
        fields = " ".join(['uid', 'encrypt_all', 'encrypt_key', 'hash_id',
                           'create_ts', 'update_ts', 'delete_ts',
                           'is_encrypted'])
        self.auto = namedtuple('auto', fields)

        # DATABASE SCHEMAS
        self.DBSCHEMA = {
            'user': self.user_rec,
            'friends': self.friends_rec}
