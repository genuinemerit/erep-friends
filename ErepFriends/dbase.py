# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Simple database manager for erep_friends using sqlite3.

@DEV
  Add methods to handle standard flat file writes, reads.

Module:    dbase
Class:     Dbase
Author:    PQ <pq_rfw @ pm.me>
"""
import json  # noqa: F401
import sqlite3 as sq3
from collections import namedtuple
from os import path, remove
from pathlib import Path
from pprint import pprint as pp  # noqa: F401

from cipher import Cipher
from typing import Literal
from utils import Utils

UT = Utils()
CI = Cipher()


class Dbase(object):
    """Provide functions to support database setup, usage, maintenance.

    SQLite natively supports the following types:
        NULL, INTEGER, REAL, TEXT, BLOB.
    Python equivalents are:
        None, int, float, string, byte
    """

    def __init__(self, ST):
        """Initialize Dbase object

        Args:
            ST (object): Instantiated Structs object
        """
        self.ST = ST

# TYPES

    class Types(object):
        """Define non-standard data types."""

        dbaction = Literal['add', 'upd', 'del']
        tblnames = Literal['config', 'user', 'friends']

    def config_main_db(self):
        """Define main database configuration."""
        self.ST.ConfigFields.main_db_path =\
            path.abspath(path.realpath(self.ST.ConfigFields.db_dir_path))
        if not Path(self.ST.ConfigFields.main_db_path).exists():
            msg = self.ST.ConfigFields.main_db_path +\
                " could not be reached"
            raise Exception(OSError, msg)
        self.ST.ConfigFields.main_db =\
            path.join(self.ST.ConfigFields.main_db_path,
                      self.ST.ConfigFields.db_name)

    def disconnect_dmain(self):
        """Drop connection to main database at configured path."""
        if hasattr(self, "dmain_conn") and self.dmain_conn is not None:
            try:
                self.dmain_conn.close()
            except RuntimeWarning:
                pass
        self.dmain_conn = None

    def connect_dmain(self):
        """Open connection to main database at configured path.

        Create a db file if one does not already exist.
        """
        self.disconnect_dmain()
        self.dmain_conn = sq3.connect(self.ST.ConfigFields.main_db)

    def get_data_keys(self, p_tbl_nm: Types.tblnames) -> list:
        """Get column names for selected DB table.

        Args:
            p_tbl_nm (Types.tblnames): config, user or friends
        Returns:
            list: of "data" dataclass column names
        """
        data_keys =\
            self.ST.ConfigFields.keys() if p_tbl_nm == 'config'\
            else self.ST.UserFields.keys() if p_tbl_nm == 'user'\
            else self.ST.FriendsFields.keys()
        return data_keys

    def create_tables(self):
        """Create DB tables on main database.

        Raises:
            Fail if cursor connection has not been established.
        """
        self.connect_dmain()
        cur = self.dmain_conn.cursor()
        for tbl_nm in ['config', 'user', 'friends']:
            sql = "SELECT name FROM sqlite_master " +\
                "WHERE type='table' AND name='{}';".format(tbl_nm)
            cur.execute(sql)
            result = cur.fetchall()
            if len(result) == 0:
                data_keys = self.get_data_keys(tbl_nm)
                col_nms = [*data_keys, *self.ST.AuditFields.keys()]
                for col in col_nms:
                    ix = col_nms.index(col)
                    if col == "encrypt_key":
                        col_nms[ix] = col + " BLOB"
                    else:
                        col_nms[ix] = col + " TEXT"
                    if col in ("create_ts", "hash_id"):
                        col_nms[ix] += " NOT NULL"
                    if col == "uid":
                        col_nms[ix] += " PRIMARY KEY"
                sql = "CREATE TABLE {}({});".format(tbl_nm, ", ".join(col_nms))
                cur.execute(sql)
        cur.close()
        self.dmain_conn.commit()
        self.disconnect_dmain()

    def set_insert_sql(self,
                       p_tbl_nm: Types.tblnames,
                       dat_col_nms: list,
                       dat_col_vals: object,
                       aud_col_nms: list,
                       aud_col_vals: object) -> str:
        """Format SQL for an INSERT.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, friends, config
            dat_col_nms (list): of column names in the "data" class
            dat_col_vals (object): "data" dataclass
            aud_col_nms (list): of column names in the "audit" class
            aud_col_vals (object): "audit" dataclass

        Returns:
            str: formatted SQL to execute
        """
        sql_cols = ", ".join([*dat_col_nms, *aud_col_nms])
        sql_vals = ""
        for cnm in dat_col_nms:
            val = getattr(dat_col_vals, cnm)
            if cnm == "encrypt_key":
                sql_vals += "?, "
            elif val is None:
                sql_vals += "NULL, "
            else:
                sql_vals += "'{}', ".format(val)
        for cnm in aud_col_nms:
            val = getattr(aud_col_vals, cnm)
            if val is None:
                sql_vals += "NULL, "
            else:
                sql_vals += "'{}', ".format(val)
        sql = "INSERT INTO {} ({}) VALUES ({});".format(p_tbl_nm,
                                                        sql_cols,
                                                        sql_vals[:-2])
        return(sql)

    def hash_and_encrypt(self,
                         p_tbl_nm: Types.tblnames,
                         p_dat_col_nms: list,
                         p_dat_col_vals: object,
                         p_aud_col_vals: object,
                         p_encrypt_all: str,
                         p_encrypt_key: str) -> tuple:
        """Hash and encrypt a data row as needed.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, friends, config
            p_data (object): a "data" dataclass
            p_uid (string, optional): Required for upd, del. Default is None.
            p_encrypt (bool, optional): For friends only. If True, encrypt
              "data" fields. user "data" always encrypted. Default is False.

        Returns:
            tuple of updated (dataclass("audit), dataclass("data"))
        """
        dat_col_vals = p_dat_col_vals
        aud_col_vals = p_aud_col_vals
        hash_str = ""
        hash_flds = (cnm for cnm in p_dat_col_nms if cnm != "encrypt_key")
        for cnm in hash_flds:
            val = str(getattr(dat_col_vals, cnm))
            if val not in (None, "None", ""):            # then hash
                hash_str += val
                if aud_col_vals.is_encrypted == "True":  # and encrypt
                    encrypt_val = CI.encrypt(val, p_encrypt_key)
                    setattr(dat_col_vals, cnm, encrypt_val)
        aud_col_vals.hash_id = UT.get_hash(hash_str)
        return(dat_col_vals, aud_col_vals)

    def insert_db(self,
                  p_tbl_nm: Types.tblnames,
                  p_data: object,
                  p_encrypt: bool) -> tuple:
        """Insert one row to main database.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, friends, config
            p_data (object): a "data" dataclass
            p_encrypt (bool, optional): For friends table only. If True,
                encrypt "data". user table always encrypted. Default is False.

        Returns:
            tuple: (list(col_nms), dataclass("data"), str(sql))
        """
        aud_col_nms = self.ST.AuditFields.keys()
        aud_col_vals = self.ST.AuditFields
        dat_col_nms = self.get_data_keys(p_tbl_nm)
        dat_col_vals = p_data
        aud_col_vals.uid = UT.get_uid()
        dttm = UT.get_dttm('UTC')
        aud_col_vals.create_ts = dttm.curr_utc
        aud_col_vals.update_ts = dttm.curr_utc
        aud_col_vals.delete_ts = None
        encrypt_all = False
        encrypt_key = None
        if p_tbl_nm == "user":
            dat_col_vals.encrypt_key = CI.set_key()
            encrypt_key = dat_col_vals.encrypt_key
            encrypt_all = dat_col_vals.encrypt_all
        elif p_tbl_nm == "friends":
            user_rec = self.query_user()
            encrypt_key = user_rec[0]["data"].encrypt_key
            encrypt_all = user_rec[0]["data"].encrypt_all
        if p_encrypt or encrypt_all in (True, "True"):
            aud_col_vals.is_encrypted = "True"
        dat_col_vals, aud_col_vals =\
            self.hash_and_encrypt(p_tbl_nm,
                                  dat_col_nms, dat_col_vals,
                                  aud_col_vals,
                                  encrypt_all, encrypt_key)
        sql = self.set_insert_sql(p_tbl_nm,
                                  dat_col_nms, dat_col_vals,
                                  aud_col_nms, aud_col_vals)
        return(dat_col_nms, dat_col_vals, sql)

    def write_db(self,
                 p_db_action: Types.dbaction,
                 p_tbl_nm: Types.tblnames,
                 p_data: object,
                 p_uid: str = None,
                 p_encrypt: bool = False):
        """Write a record to the DB.

        Args:
            p_db_action (Types.dbaction -> str): add, upd, del
            p_tbl_nm (Types.tblnames -> str): user, friends, config
            p_data (object): a "data" dataclass
            p_uid (string, optional): Required for upd, del. Default is None.
            p_encrypt (bool, optional): For friends only. If True, encrypt
              "data" fields. user "data" always encrypted. Default is False.
        """
        if p_db_action == "add":
            dat_col_nms, dat_col_vals, sql =\
                self.insert_db(p_tbl_nm, p_data, p_encrypt)
        self.connect_dmain()
        cur = self.dmain_conn.cursor()
        if "encrypt_key" in dat_col_nms:
            try:
                cur.execute(sql, [dat_col_vals.encrypt_key])
                self.dmain_conn.commit()
            except IOError:
                print("SQL execution failed")
        else:
            try:
                cur.execute(sql)
                self.dmain_conn.commit()
            except IOError:
                print("SQL execution failed")
        self.dmain_conn.close()

    def decrypt_query_result(self,
                             p_tbl_nm: Types.tblnames,
                             p_data_list: list) -> list:
        """If data is encrypted, unencrypt it.

        Args:
            p_tbl_nm (Types.tblnames -> str): config, user, friends
            p_data_list (list): encrypted list of dataclass results

        Returns:
            list: decrypted list of dataclass-formatted results
        """
        if p_tbl_nm == "user":
            encrypt_key = p_data_list["data"][0].encrypt_key
        else:
            user_rec = CN.get_user_data()
            if not user_rec:
                msg = "User record not found"
                raise Exception(ValueError, msg)
            encrypt_key = user_rec["data"].encrypt_key
        data_keys = self.get_data_keys(p_tbl_nm)
        col_nms = (cnm for cnm in data_keys if cnm != "encrypt_key")
        data_list = list()
        for ix, row in enumerate(p_data_list):
            for cnm in col_nms:
                encrypted_val = getattr(row["data"], cnm)
                decrypt_val = CI.decrypt(encrypted_val, encrypt_key)
                setattr(row["data"], cnm, decrypt_val)
                data_list[ix] = row
        return(data_list)

    def format_query_result(self,
                            p_tbl_nm: Types.tblnames,
                            p_decrypt: bool,
                            p_col_nms: list,
                            p_result: list) -> list:
        """Convert sqlite3 results into local format.

        Sqlite returns each row as a tuple in a list.
        When no rows are found, sqlite return a tuple with
          all values set to None, which is odd since then
          we get a rowcount > 0. Sqlite also appears to
          return an extra timestamp value at the end of
          the row.
        To facilitate data management on the return side,
          cast each row into a dataclass and put those in list,
          ignoring the row if it is all None values.

        Args:
            p_tbl_nm (Types.tblnames -> str): config, user, friends
            p_decrypt (bool): True if results should be decrypted
            p_col_nms (list): list of all col names on the row
            p_result (sqlite result set -> list): list of tuples

        Returns:
            list: each containing a dict of "data" and "audit" dataclass
        """
        data_list = list()
        for row in p_result:
            data_keys = self.get_data_keys(p_tbl_nm)
            data_vals = self.ST.ConfigFields if p_tbl_nm == 'config'\
                        else self.ST.UserFields if p_tbl_nm == 'user'\
                        else self.ST.FriendsFields
            data_row = {"data": data_vals, "audit": self.ST.AuditFields}
            all_none = True
            max_col_ix = len(p_col_nms) - 1
            for col_ix, val in enumerate(row):
                if col_ix > max_col_ix:
                    break
                all_none = False if val is not None else all_none
                col_nm = p_col_nms[col_ix]
                if col_nm in data_keys:
                    setattr(data_row["data"], col_nm, val)
                else:
                    setattr(data_row["audit"], col_nm, val)
            if not all_none:
                data_list.append(data_row)
        if p_decrypt and data_row["audit"].is_encrypted == 'True':
            data_list = self.decrypt_query_result(p_tbl_nm, data_list)
        return data_list

    def query_user(self, p_decrypt: bool = True) -> list:
        """Run read-only query against the user table.

        Always query for one record with max update_ts.
        We only support one active (non-deleted) user.

        Args:
            p_decrypt (bool, optional): If True, return decrypted data,
                else return data as-is on the database.

        Returns:
            list: of dataclass objects containing query results  or  empty
        """
        col_nms = [*self.ST.UserFields.keys(), *self.ST.AuditFields.keys()]
        sql = "SELECT {}, MAX(update_ts) FROM {} ".format(", ".join(col_nms),
                                                          "user")
        sql += "WHERE delete_ts IS NULL;"
        self.connect_dmain()
        cur = self.dmain_conn.cursor()
        cur_result = cur.execute(sql).fetchall()
        user_rec = self.format_query_result("user", p_decrypt,
                                            col_nms, cur_result)
        return user_rec

    def query_config(self) -> list:
        """Run read-only query against the user table.

        Always query for one record with max update_ts.
        We only support one active (non-deleted) config record.

        Returns:
            list: of dataclass objects containing query results  or  empty
        """
        col_nms = [*self.ST.ConfigFields.keys(), *self.ST.AuditFields.keys()]
        sql = "SELECT {}, MAX(update_ts) FROM {} ".format(", ".join(col_nms),
                                                          "config")
        sql += "WHERE delete_ts IS NULL;"
        self.connect_dmain()
        cur = self.dmain_conn.cursor()
        cur_result = cur.execute(sql).fetchall()
        config_rec = self.format_query_result("config", False,
                                              col_nms, cur_result)
        return config_rec






    def config_bkup_db(self,
                       p_bkup_db_path: str,
                       p_arcv_db_path: str):
        """Define DB configuration. Load values from parameters.

        Args:
            p_bkup_db_path (string): full parent path to backup db
            p_arcv_db_path (string): full parent path to archive db
        """
        self.opt.bkup_db_path =\
            path.abspath(path.realpath(p_bkup_db_path))
        if not Path(self.opt.bkup_db_path).exists():
            msg = "{} could not be reached".format(self.opt.bkup_db_path)
            raise Exception(IOError, msg)
        self.opt.bkup_db = path.join(self.opt.bkup_db_path, self.opt_db_name)
        self.opt.arcv_db_path =\
            path.abspath(path.realpath(p_arcv_db_path))
        if not Path(self.opt.arcv_db_path).exists():
            msg = "{} could not be reached".format(self.opt.arcv_db_path)
            raise Exception(IOError, msg)
        self.opt.arcv_db = path.join(self.opt.arcv_db_path, self.opt_db_name)

    def disconnect_dbkup(self):
        """Drop connection to backup database at configured path."""
        if hasattr(self, "dbkup_conn") and self.dbkup_conn is not None:
            try:
                self.dbkup_conn.close()
            except RuntimeWarning:
                pass
        self.dbkup_conn = None

    def disconnect_darcv(self):
        """Drop connection to archive database at configured path."""
        if hasattr(self, "darcv_conn") and self.darcv_conn is not None:
            try:
                self.darcv_conn.close()
            except RuntimeWarning:
                pass
        self.darcv_conn = None

    def connect_dbkup(self):
        """Open connection to backup database at configured path."""
        self.disconnect_dbkup()
        dbkup = self.set_dbkup_path()
        self.dbkup_conn = sq3.connect(self.ST.CongigFields.bkup_db)

    def connect_darcv(self):
        """Open connection to archive database at configured path."""
        self.disconnect_darcv()
        darcv = self.set_darcv_path()
        self.darcv_conn = sq3.connect(self.ST.CongigFields.arcv_db)


    def backup_db(self):
        """Make full backup of the main database to the backup db.

        Create backup database file if it does not exist.
        """
        if self.opt.bkup_db_path in (None, 'None', ""):
            pass
        else:
            self.connect_dmain()
            self.connect_dbkup()
            self.dmain_conn.backup(self.dbkup_conn, pages=0, progress=None)
            self.disconnect_dmain()
            self.disconnect_dbkup()

    def archive_db(self):
        """Make full backup of main database before purging it.

        Distinct from regular backup file, a time-stamped, one-time copy.
        """
        if self.opt.arcv_db_path in (None, 'None', ""):
            pass
        else:
            self.connect_dmain()
            self.connect_darcv()
            self.dmain_conn.backup(self.darcv_conn, pages=0, progress=None)
            self.disconnect_dmain()
            self.disconnect_darcv()

    def destroy_db(self, db_path: str) -> bool:
        """Delete the specified database file.

        File to be removed must match a configured DB path

        Args:
            db_path (string): Full path to the .db file

        Returns:
            bool: True if db_path legit points to a file
        """
        main_full_path = self.set_dmain_path()
        bkup_full_path = self.set_dbkup_path()
        arcv_full_path = self.set_darcv_path()
        arcv_path = Path(arcv_full_path).parent
        destroy_full_path = path.abspath(path.realpath(db_path))
        destroy_path = Path(destroy_full_path).parent
        if destroy_full_path in (main_full_path, bkup_full_path,
                                 arcv_full_path)\
           or destroy_path == arcv_path:
            if not Path(destroy_full_path).exists():
                msg = "{} could not be reached".format(destroy_full_path)
                raise Exception(IOError, msg)
            remove(destroy_full_path)
            return True
        else:
            msg = "{} out of scope".format(destroy_full_path)
            raise Exception(IOError, msg)
        return False

    def purge_rows(self, p_uids: list, cur: object):
        """Physically delete a row from friends table on main db.

        Args:
            p_uids (list): (uids, delete_ts) tuples associated
                with rows to physically delete
            cur (object): a cursor on the main database
        """
        for row in p_uids:
            d_uid = row[0]
            d_delete_ts = row[1]
            sql = "DELETE friends WHERE uid = '{}' ".format(d_uid)
            sql += "AND delete_ts = '{}';".format(d_delete_ts)
            cur.execute(sql)

    def purge_db(self):
        """Remove rows from main db friends table."""
        self.archive_db()

        # Modify to use an appropriate purge threshold, not just
        # "deleted before today"
        dttm = UT.get_dttm()
        sql = "SELECT uid, delete_ts FROM friends "
        sql += "WHERE delete_ts < '{}' ".format(dttm.curr_utc)
        sql += "AND delete_ts IS NOT NULL;"

        self.connect_dmain()
        cur = self.dmain_conn.cursor()
        uid_list = [row for row in cur.execute(sql)]
        self.purge_rows(cur, uid_list)
        self.dmain_conn.commit()
        self.disconnect_dmain()









    def query_friends_more(self, p_sql: str,
                           p_filter: dict) -> str:
        """Build SQL to do read query on the friends table.

        - Read friends table by:
            - uid =
            - name =
            - profile_id =
            - party_name =
            - militia_name =
            - level =
            - xp =
            - or any AND combination of the above
            ... where delete_ts is NULL and MAX(update_ts)
            ... and return all columns
        - List unique values from friends table for:
            (same columns as above)
            ... where delete_ts is NULL and MAX(update_ts)

        Args:
            p_filter (dict): name/values to filter on
            p_sql (str): partially built SQL string

        Raises:
            Exception: IOError if mal-formed "LIST" request

        Returns:
            str: built-out SQL string with WHERE logic
        """
        sql = p_sql
        where_sql = list()
        for col_nm, col_val in p_filter.items():
            if col_val.upper() == "LIST" and len(list(p_filter.keys())) > 1:
                msg = "LIST must be singleton request"
                raise Exception(IOError, msg)
            where_sql.append(" {} = '{}'".format(col_nm, col_val))
        if len(where_sql) > 1:
            sql += "WHERE {}".format("AND ".join(where_sql))
            sql += " AND delete_ts IS NULL;"
        else:
            col_nm = list(p_filter.keys())[0]
            sql = "SELECT {}, ".format(col_nm)
            sql += "COUNT({}), MAX(update_ts) ".format(col_nm)
            sql += "FROM friends WHERE delete_ts IS NULL"
            sql += " GROUP BY {};".format(col_nm)
        return sql

    def query_friends(self, p_decrypt: bool = True,
                      p_filter: dict = None) -> list:
        """Run read-only queries against the friends table.

        - AND logic is is used when multiple colums are queried.
        - No JOIN or OR logic supported.
        - GROUP BY is triggered by a search value of 'LIST'.

        Args:
            p_decrypt (bool, optional): If True, return decrypted data,
                else return data as-is on the database.
            p_filter (dict, optional): Required for friends, only for friends.
                Using col-names from self.ST.DBSCHEMA, specify 1..n columns and
                paired values. Or, single col-nm with value = "LIST".

        Returns:
            list: of dataclass objects containing query results  or  empty
        """
        col_nms = [*self.ST.DBSCHEMA["friends"].keys(),
                   *self.ST.AuditFields.keys()]
        sql = "SELECT {}, MAX(update_ts) FROM {} ".format(", ".join(col_nms),
                                                          "friends")
        sql = self.query_friends_more(sql)
        self.connect_dmain()
        cur = self.dmain_conn.cursor()
        cur_result = cur.execute(sql).fetchall()
        user_rec = self.format_query_result("friends", p_decrypt,
                                          col_nms, cur_result)
        return user_rec
