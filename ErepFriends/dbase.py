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
from copy import copy
from os import path, remove
from pathlib import Path
from pprint import pprint as pp  # noqa: F401
from typing import Literal

from cipher import Cipher
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

    def connect_dmain(self, p_main_db):
        """Open connection to main database at configured path.

        Create a db file if one does not already exist.

        Args:
            p_main_db (str): full path to main db file
        """
        self.disconnect_dmain()
        self.dmain_conn = sq3.connect(p_main_db)

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
        self.connect_dmain(self.ST.ConfigFields.main_db)
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
                    if col == "hash_id":
                        col_nms[ix] += " PRIMARY KEY"
                sql = "CREATE TABLE {}({});".format(tbl_nm, ", ".join(col_nms))
                cur.execute(sql)
        cur.close()
        self.dmain_conn.commit()
        self.disconnect_dmain()

    def set_insert_sql(self,
                       p_tbl_nm: Types.tblnames,
                       p_data_rec: list,
                       p_audit_rec: list) -> str:
        """Format SQL for an INSERT.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, friends, configs
            data_rec (list): mirrors an "data" dataclass
            audit_rec (list): mirrors the "audit" dataclass

        Returns:
            str: formatted SQL to execute
        """
        sql_cols = ", ".join([*p_data_rec.keys(),
                              *self.ST.AuditFields.keys()])
        sql_vals = ""
        for cnm, val in p_data_rec.items():
            if cnm == "encrypt_key":
                sql_vals += "?, "
            elif val is None:
                sql_vals += "NULL, "
            else:
                sql_vals += "'{}', ".format(val)
        for cnm in self.ST.AuditFields.keys():
            val = p_audit_rec[cnm]
            if val is None:
                sql_vals += "NULL, "
            else:
                sql_vals += "'{}', ".format(val)
        sql = "INSERT INTO {} ({}) VALUES ({});".format(p_tbl_nm,
                                                        sql_cols,
                                                        sql_vals[:-2])
        return(sql)

    def hash_and_encrypt(self,
                         p_data_rec: dict,
                         p_audit_rec: dict,
                         p_encrypt_key: str) -> tuple:
        """Hash and encrypt a data row as needed.

        Args:
            p_data_rec (dict): mirrors "data" dataclass
            p_audit_rec (dict): mirrors "audit" dataclass
            p_encrypt_key (str): user's encryption key

        Returns:
            tuple of updated (dataclass("audit), dataclass("data"))
        """
        # Store modified values
        data_rec = p_data_rec
        audit_rec = p_audit_rec
        hash_str = ""
        # Double-check this logic to make sure it is working.
        # I seem to be getting inserts even when all values are the same.
        for cnm, val in p_data_rec.items():
            if cnm != "encrypt_key"\
            and val not in (None, "None", ""):             # then hash
                hash_str += val
                if p_audit_rec["is_encrypted"] == "True":  # and encrypt
                    data_rec[cnm] = CI.encrypt(val, p_encrypt_key)
        audit_rec["hash_id"] = UT.get_hash(hash_str)
        return(data_rec, audit_rec)

    def get_encrypt_key(self,
                        p_tbl_nm: Types.tblnames,
                        p_encrypt_all: bool = False) -> tuple:
        """Get the encrypt key and encrypt-all setting.

        Args:
            p_tbl_nm (Types.tblnames): name of table being modified
            p_encrypt_all (bool): selected setting. Use only if table
                is user. Default is False.

        Returns:
            tuple: (str: encrypt_key, bool: encrypt_all)
        """
        encrypt_key = None
        encrypt_all = False
        if p_tbl_nm == "user":
            encrypt_key = CI.set_key()
            encrypt_all = p_encrypt_all
        elif p_tbl_nm == "friends":
            user_rec = self.query_user()
            encrypt_key = user_rec["data"].encrypt_key
            encrypt_all = user_rec["data"].encrypt_all
        return(encrypt_key, encrypt_all)

    def set_insert_data(self,
                  p_tbl_nm: Types.tblnames,
                  p_data_rec: dict,
                  p_encrypt: bool) -> tuple:
        """Format one logically new row for main database.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, friends, config
            p_data_rec (dict): mirrors a "data" dataclass
            p_encrypt (bool, optional): For friends table only. If True,
                encrypt "data". user table always encrypted. Default is False.

        Returns:
            tuple: (dict: data_rec, dict: audit_rec)
        """
        audit_rec = dict()
        for cnm in self.ST.AuditFields.keys():
            audit_rec[cnm] = copy(getattr(self.ST.AuditFields, cnm))
        audit_rec["pid"] = UT.get_uid()
        dttm = UT.get_dttm('UTC')
        audit_rec["create_ts"] = dttm.curr_utc
        audit_rec["update_ts"] = dttm.curr_utc
        audit_rec["delete_ts"] = None

        encrypt_all = p_data_rec["encrypt_all"]\
                      if p_tbl_nm == 'user' else False
        encrypt_key, encrypt_all = self.get_encrypt_key(p_tbl_nm, encrypt_all)
        if p_encrypt or encrypt_all in (True, "True"):
            audit_rec["is_encrypted"] = "True"
        data_rec, audit_rec =\
            self.hash_and_encrypt(p_data_rec, audit_rec, encrypt_key)
        return(data_rec, audit_rec)

    def set_upsert_data(self,
                  p_tbl_nm: Types.tblnames,
                  p_data: dict,
                  p_pid: str,
                  p_encrypt: bool) -> tuple:
        """Format one logically updated row to main database.

        Do nothing if no value-changes are detected.

        @DEV 1 - test the "no change" logic more carefully.
         Either it is not noticing that there is no change or
         different hashes are being generated for the same data.

        @DEV 2 - start updating the delete_ts for obsoleted records.
         This will be a physical UPDATE based on read by PK (hash_id)

        Args:
            p_tbl_nm (Types.tblnames -> str): user, friends, config
            p_data (dict): that mirrors a "data" dataclass
            p_pid (str): Unique Identifier of record to be updated
            p_encrypt (bool, optional): For friends table only. If True,
                encrypt "data". user table always encrypted. Default is False.

        Returns:
            tuple: (dict: data_rec, dict: audit_rec)
        """
        if p_tbl_nm == 'config':
            db_rec = self.query_config()
        elif p_tbl_nm == 'user':
            db_rec = self.query_user()
        # else query friends for latest record with pid = p_pid
        if not db_rec or db_rec["audit"].pid != p_pid:
            msg = "Cannot upsert. Record not found or ID not matched."
            raise Exception(ValueError, msg)

        audit_rec = dict()
        for cnm in self.ST.AuditFields.keys():
            audit_rec[cnm] = copy(getattr(db_rec["audit"], cnm))
        dttm = UT.get_dttm('UTC')
        audit_rec['update_ts'] = dttm.curr_utc

        encrypt_all = p_data["encrypt_all"] if p_tbl_nm == 'user' else False
        encrypt_key, encrypt_all = self.get_encrypt_key(p_tbl_nm, encrypt_all)
        if p_encrypt or encrypt_all in (True, "True"):
            audit_rec["is_encrypted"] = "True"
        data_rec, audit_rec =\
            self.hash_and_encrypt(p_data, audit_rec, encrypt_key)
        # Double-check this logic to make sure it is working
        # I seem to be getting inserts even when all values are the same.
        if db_rec["audit"].hash_id == audit_rec["hash_id"]:
            return(None, None)
        return(data_rec, audit_rec)

    def write_db(self,
                 p_db_action: Types.dbaction,
                 p_tbl_nm: Types.tblnames,
                 p_data: dict,
                 p_pid: str = None,
                 p_encrypt: bool = False):
        """Write a record to the DB.

        Args:
            p_db_action (Types.dbaction -> str): add, upd, del
            p_tbl_nm (Types.tblnames -> str): user, friends, config
            p_data (dict): a dict that mirrors a "data" dataclass
            p_pid (string, optional): Required for upd, del. Default is None.
            p_encrypt (bool, optional): For friends only. If True, encrypt
              "data" fields. user "data" always encrypted. Default is False.
        """
        if p_db_action == "add":
            data_rec, audit_rec = self.set_insert_data(p_tbl_nm, p_data, p_encrypt)
        elif p_db_action == "upd":
            data_rec, audit_rec =\
                self.set_upsert_data(p_tbl_nm, p_data, p_pid, p_encrypt)
        if data_rec is not None and audit_rec is not None:
            sql = self.set_insert_sql(p_tbl_nm, data_rec, audit_rec)
            encrypt_key = data_rec["encrypt_key"]\
                if "encrypt_key" in data_rec.keys() else False
            if sql:
                self.connect_dmain(self.ST.ConfigFields.main_db)
                cur = self.dmain_conn.cursor()
                if encrypt_key:
                    try:
                        cur.execute(sql, [encrypt_key])
                        self.dmain_conn.commit()
                    except IOError:
                        self.dmain_conn.close()
                else:
                    try:
                        cur.execute(sql)
                        self.dmain_conn.commit()
                    except IOError:
                        self.dmain_conn.close()
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
            user_rec = self.query_user()
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
        cfgd = self.query_config()
        self.connect_dmain(cfgd["data"].main_db)
        cur = self.dmain_conn.cursor()
        cur_result = cur.execute(sql).fetchall()
        user_rec = self.format_query_result("user", p_decrypt,
                                            col_nms, cur_result)

        user_rec = user_rec[0] if len(user_rec) > 0 else user_rec
        return user_rec

    def query_config(self) -> list:
        """Run read-only query against the user table.

        Always query for one record with max update_ts.
        We only support one active (non-deleted) config record.
        On successful query, return result and also refresh
          config data in Structs object.

        Returns:
            list: of dataclass objects containing query results  or  empty
        """
        col_nms = [*self.ST.ConfigFields.keys(), *self.ST.AuditFields.keys()]
        sql = "SELECT {}, MAX(update_ts) FROM {} ".format(", ".join(col_nms),
                                                          "config")
        sql += "WHERE delete_ts IS NULL;"
        self.connect_dmain(self.ST.ConfigFields.main_db)
        cur = self.dmain_conn.cursor()
        cur_result = cur.execute(sql).fetchall()
        config_rec = self.format_query_result("config", False,
                                              col_nms, cur_result)
        if len(config_rec) > 0:
            cfg_data = config_rec[0]["data"]
            for cnm in self.ST.ConfigFields.keys():
                setattr(self.ST.ConfigFields, cnm, getattr(cfg_data, cnm))
        config_rec = config_rec[0] if len(config_rec) > 0 else config_rec
        return config_rec

    def config_bkup_db(self,
                       p_bkup_db_path: str) -> tuple:
        """Define DB configuration. Load values from parameters.

        Args:
            p_bkup_db_path (string): full parent path to backup dbs
        Returns:
            tuple: (str: full bkup db dir, str: full arcv db dir,
                    str: full bkup db path, str: full arcv db path)
        """
        # backup database
        bkup_db_path = path.abspath(path.realpath(p_bkup_db_path))
        if not Path(bkup_db_path).exists():
            msg = p_bkup_db_path + " could not be reached"
            raise Exception(IOError, msg)
        bkup_db = path.join(bkup_db_path,
                            self.ST.ConfigFields.db_name)
        # archive databases
        arcv_db_path = bkup_db_path
        arcv_db = path.join(arcv_db_path,
                            self.ST.ConfigFields.db_name)
        return(bkup_db_path, arcv_db_path, bkup_db, arcv_db)

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

    def connect_dbkup(self, p_bkup_db):
        """Open connection to backup database at configured path.

        Args:
            p_bkup_db (str): full path to backup DB file
        """
        self.disconnect_dbkup()
        self.dbkup_conn = sq3.connect(p_bkup_db)

    def connect_darcv(self, p_arcv_db):
        """Open connection to archive database at configured path.

        Args:
            p_arcv_db (str): full path to archive DB file
        """
        self.disconnect_darcv()
        self.darcv_conn = sq3.connect(p_arcv_db)

    def backup_db(self):
        """Make full backup of the main database to the backup db.

        Creates a backup database file if it does not exist, else
          overwrites it.
        """
        cfgd = self.query_config()
        if cfgd["data"].bkup_db\
        and cfgd["data"].bkup_db not in (None, 'None'):
            self.connect_dmain(cfgd["data"].main_db)
            self.connect_dbkup(cfgd["data"].bkup_db)
            self.dmain_conn.backup(self.dbkup_conn, pages=0, progress=None)
            self.disconnect_dmain()
            self.disconnect_dbkup()

    def archive_db(self):
        """Make full backup of main database witha timestamp.

        Distinct from regular backup file. A time-stamped, one-time copy.
        Use this to make a point-in-time copy or prior to doing a purge.
        """
        cfgd = self.query_config()
        if cfgd["data"].arcv_db\
        and cfgd["data"].arcv_db not in (None, 'None'):
            dttm = UT.get_dttm('UTC')
            arcv_db = cfgd["data"].arcv_db + "." + dttm.curr_ts
            self.connect_dmain(cfgd["data"].main_db)
            self.connect_darcv(arcv_db)
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

    def purge_rows(self, p_pids: list, cur: object):
        """Physically delete a row from friends table on main db.

        Args:
            p_pids (list): (pids, delete_ts) tuples associated
                with rows to physically delete
            cur (object): a cursor on the main database
        """
        for row in p_pids:
            d_pid = row[0]
            d_delete_ts = row[1]
            sql = "DELETE friends WHERE uid = '{}' ".format(d_pid)
            sql += "AND delete_ts = '{}';".format(d_delete_ts)
            cur.execute(sql)

    def purge_db(self):
        """Remove rows from main db friends table."""
        self.archive_db()

        # Modify to use an appropriate purge threshold, not just
        # "deleted before today"
        dttm = UT.get_dttm()
        sql = "SELECT pid, delete_ts FROM friends "
        sql += "WHERE delete_ts < '{}' ".format(dttm.curr_utc)
        sql += "AND delete_ts IS NOT NULL;"

        cfgd = self.query_config()
        self.connect_dmain(cfgd["data"].main_db)
        cur = self.dmain_conn.cursor()
        pid_list = [row for row in cur.execute(sql)]
        self.purge_rows(cur, pid_list)
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
        cfgd = self.query_config()
        self.connect_dmain(cfgd["data"].main_db)
        cur = self.dmain_conn.cursor()
        cur_result = cur.execute(sql).fetchall()
        user_rec = self.format_query_result("friends", p_decrypt,
                                          col_nms, cur_result)
        return user_rec
