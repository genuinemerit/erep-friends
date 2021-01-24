# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Simple database manager for ErepFriends using sqlite3.

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


    class Types(object):
        """Define non-standard data types."""

        dbaction = Literal['add', 'upd', 'del']
        tblnames = Literal['config', 'user', 'citizen', 'texts']

    def config_main_db(self):
        """Define main database location."""
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
        """Get "data" class column names for selected DB table.

        Args:
            p_tbl_nm (Types.tblnames): config, user or citizen
        Returns:
            list: of "data" dataclass column names
        """
        data_keys =\
            self.ST.ConfigFields.keys() if p_tbl_nm == 'config'\
            else self.ST.UserFields.keys() if p_tbl_nm == 'user'\
            else self.ST.TextFields.keys() if p_tbl_nm == 'texts'\
            else self.ST.CitizenFields.keys()
        return data_keys

    def create_tables(self):
        """Create DB tables on main database.

        Raises:
            Fail if cursor connection has not been established.
        """
        self.connect_dmain(self.ST.ConfigFields.main_db)
        cur = self.dmain_conn.cursor()
        for tbl_nm in ['config', 'user', 'citizen', 'texts']:
            # Does table already exist?
            sql = "SELECT name FROM sqlite_master " +\
                "WHERE type='table' AND name='{}';".format(tbl_nm)
            cur.execute(sql)
            result = cur.fetchall()
            # No...
            if len(result) == 0:
                data_keys = self.get_data_keys(tbl_nm)
                col_nms = [*data_keys, *self.ST.AuditFields.keys()]
                for ix, col in enumerate(col_nms):
                    # ix = col_nms.index(col)
                    if col == "encrypt_key":
                        col_nms[ix] = col + " BLOB"
                    else:
                        col_nms[ix] = col + " TEXT"
                    if col in ("pid", "uid", "create_ts", "hash_id"):
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
                       p_data_rec: dict,
                       p_audit_rec: dict) -> str:
        """Format SQL for an INSERT.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, citizen, configs
            p_data_rec (dict): mirrors an "data" dataclass
            p_audit_rec (dict): mirrors the "audit" dataclass

        Returns:
            str: formatted SQL to execute
        """
        sql_cols = ", ".join([*p_data_rec.keys(), *p_audit_rec.keys()])
        sql_vals = ""
        for cnm, val in p_data_rec.items():
            if cnm == "encrypt_key":
                sql_vals += "?, "
            elif val is None:
                sql_vals += "NULL, "
            else:
                sql_vals += "'{}', ".format(val)
        for cnm, val in p_audit_rec.items():
            if val is None:
                sql_vals += "NULL, "
            else:
                sql_vals += "'{}', ".format(val)
        sql = "INSERT INTO {} ({}) VALUES ({});".format(p_tbl_nm,
                                                        sql_cols,
                                                        sql_vals[:-2])
        return(sql)

    def hash_data_values(self,
                         p_data_rec: dict,
                         p_audit_rec: dict) -> tuple:
        """Hash a data row as needed.

        Args:
            p_data_rec (dict): mirrors "data" dataclass
            p_audit_rec (dict): mirrors "audit" dataclass

        Returns:
            tuple of updated (dataclass("audit), dataclass("data"))
        """
        data_rec = p_data_rec
        audit_rec = p_audit_rec
        hash_str = ""
        for cnm, val in p_data_rec.items():
            if cnm != "encrypt_key"\
            and val not in (None, "None", ""):
                hash_str += str(val)
        audit_rec["hash_id"] = UT.get_hash(hash_str)
        return(data_rec, audit_rec)

    def encrypt_data_values(self,
                         p_data: dict) -> dict:
        """Encrypt a data on a user table row.

        Args:
            p_data (dict): mirrors "data" dataclass

        Returns:
            dict: updated / encrypted "data" row
        """
        data_rec = p_data
        for cnm, val in p_data.items():
            if cnm != "encrypt_key"\
            and val not in (None, "None", ""):
                data_rec[cnm] = CI.encrypt(str(val), p_data["encrypt_key"])
        return data_rec

    def query_latest(self,
                     p_tbl_nm: Types.tblnames,
                     p_pid: str = None,
                     p_single: bool = True):
        """Get the latest non-deleted record(s) for selected table.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, citizen, config, texts
            p_pid (str): Ignored except for citizen, when it is required.
            p_single (bool): If True, return only latest row even if there are
                             multiples with NULL delete_ts. If False, return
                             all latest rows that have a NULL delete_ts.

        Returns:
            dict ("data": ..., "audit", ...) for user, config or texts
            list (of dicts like this ^) for citizen
        """
        db_recs = None
        if p_tbl_nm == "user":
            db_recs = self.query_user(p_single)
        elif p_tbl_nm == "config":
            db_recs = self.query_config(p_single)
        elif p_tbl_nm == "texts":
            db_recs = self.query_texts(p_single)
        elif p_tbl_nm == "citizen":
            db_recs = self.query_citizen_by_pid(p_pid)
        return db_recs

    def set_insert_data(self,
                  p_tbl_nm: Types.tblnames,
                  p_data: dict) -> tuple:
        """Format one logically new row for main database.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, citizen, config, texts
            p_data (dict): mirrors a "data" dataclass

        Returns:
            tuple: (dict: data_rec, dict: audit_rec)
        """
        audit_rec = dict()
        for cnm in self.ST.AuditFields.keys():
            audit_rec[cnm] = copy(getattr(self.ST.AuditFields, cnm))
        audit_rec["uid"] = UT.get_uid()
        audit_rec["pid"] = UT.get_uid()
        dttm = UT.get_dttm('UTC')
        audit_rec["create_ts"] = dttm.curr_utc
        audit_rec["update_ts"] = dttm.curr_utc
        audit_rec["delete_ts"] = None
        data_rec, audit_rec =\
            self.hash_data_values(p_data, audit_rec)
        recs = self.query_latest(p_tbl_nm, audit_rec["pid"])
        if recs is not None:
            aud = UT.make_namedtuple("aud", recs["audit"])
            if aud.hash_id == audit_rec["hash_id"]:
                return(None, None)
        if p_tbl_nm == "user":
            p_data["encrypt_key"] = CI.set_key()
            data_rec = self.encrypt_data_values(p_data)
        return(data_rec, audit_rec)

    def set_upsert_data(self,
                  p_tbl_nm: Types.tblnames,
                  p_data: dict,
                  p_pid: str) -> tuple:
        """Format one logically updated row to main database.

        Do nothing if no value-changes are detected.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, citizen, config
            p_data (dict): that mirrors a "data" dataclass
            p_pid (str): Unique Identifier of record to be updated

        Returns:
            tuple: (dict: data_rec, dict: audit_rec)
        """
        recs = self.query_latest(p_tbl_nm, p_pid)
        aud = UT.make_namedtuple("aud", recs["audit"])
        dat = UT.make_namedtuple("dat", recs["data"])
        if not aud or aud.pid != p_pid:
            msg = "Cannot upsert. Record not found or PID not matched."
            raise Exception(ValueError, msg)
        audit_rec = UT.make_dict(self.ST.AuditFields.keys(), aud)
        audit_rec["uid"] = UT.get_uid()
        audit_rec['pid'] = copy(aud.pid)
        audit_rec['create_ts'] = copy(aud.create_ts)
        dttm = UT.get_dttm('UTC')
        audit_rec['update_ts'] = dttm.curr_utc
        if p_tbl_nm == "user" and p_data["encrypt_key"] in (None, "None", ""):
            p_data["encrypt_key"] = copy(dat.encrypt_key)
        data_rec, audit_rec =\
            self.hash_data_values(p_data, audit_rec)
        if p_tbl_nm == "user":
            data_rec = self.encrypt_data_values(p_data)
        if aud.hash_id == audit_rec["hash_id"]:
            return(None, None, None)
        return(data_rec, audit_rec, aud.hash_id)

    def set_logical_delete_sql(self,
                               p_tbl_nm: Types.tblnames,
                               p_pid: str):
        """Set value of delete_ts on the previously-active record."""
        recs = self.query_latest(p_tbl_nm, p_pid, False)
        aud = UT.make_namedtuple("aud", recs[0]["audit"])
        dttm = UT.get_dttm('UTC')
        sql = "UPDATE {}".format(p_tbl_nm)
        sql += " SET delete_ts = '{}'".format(dttm.curr_utc)
        sql += " WHERE uid = '{}';".format(aud.uid)
        return sql

    def execute_txn_sql(self,
                        p_db_action: Types.dbaction,
                        p_tbl_nm: Types.tblnames,
                        p_sql: str,
                        p_pid: str = None,
                        p_encrypt_key: str = None):
        """Execute SQL to modify the database content.

        Args:
            p_db_action (Types.dbaction -> string): add, upd, del
            p_tbl_nm (Types.tblnames -> str): user, citizen, config, texts
            p_sql (string): the SQL statement to execute
            p_pid (string): if updating a record, used to delete previous
            p_encrypt_key (string): if adding or updating a user record
        """
        self.connect_dmain(self.ST.ConfigFields.main_db)
        cur = self.dmain_conn.cursor()
        if p_encrypt_key:
            try:
                cur.execute(p_sql, [p_encrypt_key])
                self.dmain_conn.commit()
            except IOError:
                self.dmain_conn.close()
        else:
            try:
                cur.execute(p_sql)
                self.dmain_conn.commit()
            except IOError:
                self.dmain_conn.close()
        self.dmain_conn.close()
        if p_db_action == "upd":
            self.write_db("del", p_tbl_nm, None, p_pid)

    def write_db(self,
                 p_db_action: Types.dbaction,
                 p_tbl_nm: Types.tblnames,
                 p_data: dict = None,
                 p_pid: str = None):
        """Write a record to the DB.

        Args:
            p_db_action (Types.dbaction -> str): add, upd, del
            p_tbl_nm (Types.tblnames -> str): user, citizen, config, texts
            p_data (dict): mirrors a "data" dataclass. None if "del".
            p_pid (string): Required for upd, del. Default is None.
        """
        if p_db_action == "add":
            data_rec, audit_rec = self.set_insert_data(p_tbl_nm, p_data)
        elif p_db_action == "upd":
            data_rec, audit_rec, prev_hash_id =\
                self.set_upsert_data(p_tbl_nm, p_data, p_pid)
        sql = ""
        encrypt_key = ""
        if p_db_action in ("add", "upd"):
            if data_rec is not None and audit_rec is not None:
                sql = self.set_insert_sql(p_tbl_nm, data_rec, audit_rec)
                encrypt_key = data_rec["encrypt_key"]\
                    if "encrypt_key" in data_rec.keys() else False
        elif p_db_action == "del":
            sql = self.set_logical_delete_sql(p_tbl_nm, p_pid)
        if sql:
            self.execute_txn_sql(p_db_action, p_tbl_nm, sql,
                                 p_pid, encrypt_key)

    def decrypt_user_data(self,
                          p_user_data: dict) -> dict:
        """Unencrypt user row data.

        Args:
            p_user_data (dict): encrypted "data" info for user table

        Returns:
            dict: decrypted "data" info
        """
        user_data = copy(p_user_data)
        encrypt_key = user_data["encrypt_key"]
        data_keys = self.ST.UserFields.keys()
        data_keys.remove("encrypt_key")
        for cnm in data_keys:
            user_data[cnm] = CI.decrypt(user_data[cnm], encrypt_key)
        return(user_data)

    def format_query_result(self,
                            p_tbl_nm: Types.tblnames,
                            p_result: list) -> list:
        """Convert sqlite3 results into local format.

        Sqlite returns each row as a tuple in a list.
        When no rows are found, sqlite returns a tuple with
          all values set to None, which is odd since then
          we get a rowcount > 0. Sqlite also returns an extra
          timestamp at the end of the row.
        To facilitate data management on the return side,
          cast each row of returned data into a namedtuple that
          mirrors a dataclass and put those in a list.
          Ignore the row if it is all None values.

        Args:
            p_tbl_nm (Types.tblnames -> str): config, user, citizen, texts
            p_result (sqlite result set -> list): list of tuples

        Returns:
            list: each row is dict of dicts keyed by "data", "audit",
                  mirroring appropriate dataclass structures
        """
        def init_recs():
            dat_rec = dict()
            aud_rec = dict()
            for cnm in dat_keys:
                dat_rec[cnm] = copy(getattr(dat_dflt, cnm))
            for cnm in aud_keys:
                aud_rec[cnm] = copy(getattr(self.ST.AuditFields, cnm))
            return (dat_rec, aud_rec)

        data_out = list()
        dat_keys = self.get_data_keys(p_tbl_nm)
        aud_keys = self.ST.AuditFields.keys()
        col_nms = dat_keys + aud_keys
        dat_dflt = self.ST.ConfigFields if p_tbl_nm == 'config'\
                   else self.ST.UserFields if p_tbl_nm == 'user'\
                   else self.ST.TextFields if p_tbl_nm == 'texts'\
                   else self.ST.CitizenFields
        max_ix = len(col_nms) - 1

        for rx, in_row in enumerate(p_result):
            all_none = True
            dat_rec, aud_rec = init_recs()
            for ix, val in enumerate(in_row):
                if ix > max_ix:
                    break
                all_none = False if val is not None else all_none
                col_nm = col_nms[ix]
                if col_nm in dat_keys:
                    dat_rec[col_nm] = val
                else:
                    aud_rec[col_nm] = val
            if not all_none:
                data_out.append({"data": dat_rec, "audit": aud_rec})
        if p_tbl_nm == "user" and len(data_out) > 0:
            data_out[0]["data"] =\
                self.decrypt_user_data(data_out[0]["data"])
        return data_out

    def execute_query_sql(self,
                          p_tbl_nm: Types.tblnames,
                          p_sql: str,
                          p_single: bool =True):
        """Execute a SELECT query, with option to return only latest row.

        Args:
            p_sql (str) DB SELECT to execute
            p_tbl_nm (Types.tblnames -> str)
            p_single (bool): If True, return only the latest row

        Returns:
            dict: of (namedtuples keyed by "data", "audit")  or
            list of dicts liked that ^  or
            None if no rows found
        """
        self.connect_dmain(self.ST.ConfigFields.main_db)
        cur = self.dmain_conn.cursor()
        result = cur.execute(p_sql).fetchall()
        self.disconnect_dmain()
        data_recs = self.format_query_result(p_tbl_nm, result)
        if len(data_recs) < 1:
            data_recs = None
        elif p_single:
            data_recs = data_recs[0]
        return data_recs

    def format_query_sql(self,
                          p_tbl_nm: Types.tblnames,
                          p_single: bool = True):
        """Format a SELECT query, with option to return only latest row.

        Use this for all tables except citizen, which has different
        search criteria.

        Args:
            p_tbl_nm (Types.tblnames -> str)
            p_single (bool): If True, return only the latest row

        Returns:
            dict: of (namedtuples keyed by "data", "audit")  or
            list of dicts liked that ^  or
            None if no rows found
        """
        data_cols = self.ST.TextFields.keys() if p_tbl_nm == "texts"\
            else self.ST.ConfigFields.keys() if p_tbl_nm == "config"\
            else self.ST.UserFields.keys() if p_tbl_nm == "user"\
            else self.ST.CitizenFields.keys()
        col_nms = data_cols + self.ST.AuditFields.keys()
        sql = "SELECT {}, ".format(", ".join(col_nms))
        if p_single:
            sql += "MAX(update_ts)"
        else:
            sql = sql[:-2] # remove trailing comma and space
        sql += " FROM {} ".format(p_tbl_nm)
        sql += "WHERE delete_ts IS NULL;"
        recs = self.execute_query_sql(p_tbl_nm, sql, p_single)
        return recs

    def query_texts(self, p_single=True) -> dict:
        """Run read-only query against the texts table.

        Args:
            p_single (bool): If True, return only the latest row

        Returns:
            dict: of (namedtuples keyed by "data", "audit")
        """
        return self.format_query_sql("texts", p_single)

    def query_config(self, p_single=True) -> object:
        """Run read-only query against the user table.

        Args:
            p_single (bool): If True, return only the latest row

        Returns:
            dict: of (namedtuples keyed by "data", "audit")
        """
        return self.format_query_sql("config", p_single)

    def query_config_data(self) -> namedtuple:
        cf = self.query_config()
        cfd = UT.make_namedtuple("cfd", cf["data"])
        return cfd

    def query_user(self, p_single=True) -> dict:
        """Run read-only query against the user table.

        Args:
            p_single (bool): If True, return only the latest row

        Returns:
            dict: of (namedtuples keyed by "data", "audit")
        """
        return self.format_query_sql("user", p_single)

    def query_citizen_by_pid(self,
                             p_pid: str) -> dict:
        """Run read-only query against the citizen table.

        Return latest non-deleted record that matches on PID.

        Args:
            p_pid (str): ErepFriends DB logical object identifier

        Returns:
            dict: of (namedtuples keyed by "data", "audit")
        """
        col_nms = self.ST.CitizenFields.keys() + self.ST.AuditFields.keys()
        sql = "SELECT {}, MAX(update_ts) FROM {} ".format(", ".join(col_nms),
                                                          "citizen")
        sql += " WHERE pid = '{}'".format(str(p_pid))
        sql += " AND delete_ts is NULL;"
        recs = self.execute_query_sql("citizen", sql, p_single=True)
        return recs

    def query_citizen_by_profile_id(self,
                                    p_profile_id: str) -> dict:
        """Run read-only query against the citizen table.

        Return latest non-deleted record that matches on profile ID.

        Args:
            p_profile_id (str): eRepublik Identifier for a citizen

        Returns:
            dict: of (namedtuples keyed by "data", "audit")
        """
        col_nms = self.ST.CitizenFields.keys() + self.ST.AuditFields.keys()
        sql = "SELECT {}, MAX(update_ts) FROM {} ".format(", ".join(col_nms),
                                                          "citizen")
        sql += " WHERE profile_id = '{}'".format(str(p_profile_id))
        sql += " AND delete_ts is NULL;"
        recs = self.execute_query_sql("citizen", sql, p_single=True)
        return recs

    def config_bkup_db(self,
                       p_bkup_db_path: str) -> tuple:
        """Define DB configuration. Load values from parameters.

        Args:
            p_bkup_db_path (string): full parent path to backup dbs
        Returns:
            tuple: (str: full bkup db dir, str: full bkup db path)
        """
        bkup_db_path = path.abspath(path.realpath(p_bkup_db_path))
        if not Path(bkup_db_path).exists():
            msg = p_bkup_db_path + " could not be reached"
            raise Exception(IOError, msg)
        bkup_db = path.join(bkup_db_path, self.ST.ConfigFields.db_name)
        return(bkup_db_path, bkup_db)

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
        cfd = self.query_config_data()
        if cfd.bkup_db\
        and cfd.bkup_db not in (None, 'None'):
            self.connect_dmain(cfd.main_db)
            self.connect_dbkup(cfd.bkup_db)
            self.dmain_conn.backup(self.dbkup_conn, pages=0, progress=None)
            self.disconnect_dmain()
            self.disconnect_dbkup()

    def archive_db(self):
        """Make full backup of main database witha timestamp.

        Distinct from regular backup file. A time-stamped, one-time copy.
        Use this to make a point-in-time copy or prior to doing a purge.
        """
        cfd = self.query_config_data()
        if cfd.arcv_db\
        and cfd.arcv_db not in (None, 'None'):
            dttm = UT.get_dttm('UTC')
            arcv_db = cfd.arcv_db + "." + dttm.curr_ts
            self.connect_dmain(cfd.main_db)
            self.connect_darcv(arcv_db)
            self.dmain_conn.backup(self.darcv_conn, pages=0, progress=None)
            self.disconnect_dmain()
            self.disconnect_darcv()

    # ================  snippet code =========================

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
        """Physically delete a row from citizen table on main db.

        Args:
            p_pids (list): (pids, delete_ts) tuples associated
                with rows to physically delete
            cur (object): a cursor on the main database
        """
        for row in p_pids:
            d_pid = row[0]
            d_delete_ts = row[1]
            sql = "DELETE citizen WHERE uid = '{}' ".format(d_pid)
            sql += "AND delete_ts = '{}';".format(d_delete_ts)
            cur.execute(sql)

    def purge_db(self):
        """Remove rows from main db citizen table."""
        self.archive_db()

        # Modify to use an appropriate purge threshold, not just
        # "deleted before today"
        dttm = UT.get_dttm()
        sql = "SELECT pid, delete_ts FROM citizen "
        sql += "WHERE delete_ts < '{}' ".format(dttm.curr_utc)
        sql += "AND delete_ts IS NOT NULL;"

        cfd = self.query_config_data()
        self.connect_dmain(cfd.main_db)
        cur = self.dmain_conn.cursor()
        pid_list = [row for row in cur.execute(sql)]
        self.purge_rows(cur, pid_list)
        self.dmain_conn.commit()
        self.disconnect_dmain()

    def query_citizen(self,
                      p_filter: dict = None) -> list:
        """Run read-only queries against the citizen table.

        - AND logic is is used when multiple colums are queried.
        - No JOIN or OR logic supported.
        - GROUP BY is triggered by a search value of 'LIST'.

        Args:
            p_filter (dict, optional): Required for citizen, only for citizen.
                Using col-names from self.ST.DBSCHEMA, specify 1..n columns and
                paired values. Or, single col-nm with value = "LIST".

        Returns:
            list: of dataclass objects containing query results  or  empty
        """
        sql = "SELECT {}, MAX(update_ts) FROM {} ".format(", ".join(col_nms),
                                                          "citizen")
        sql = self.query_citizen_more(sql)
        cfd = self.query_config_data()
        self.connect_dmain(cfd.main_db)
        cur = self.dmain_conn.cursor()
        result = cur.execute(sql).fetchall()
        user_rec = self.format_query_result("citizen", result)
        return user_rec

    def query_citizen_more(self, p_sql: str,
                           p_filter: dict) -> str:
        """Build SQL to do read query on the citizen table.

        - Read citizen table by:
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
        - List unique values from citizen table for:
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
            sql += "FROM citizen WHERE delete_ts IS NULL"
            sql += " GROUP BY {};".format(col_nm)
        return sql
