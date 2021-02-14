# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Simple database manager for erep-freinds using sqlite3.

This is a write-only database system.
Records are modified only when logically deleted.
Records are removed only when a purge is run.

uid = unique identifier primary key for each row.
oid = logical identifier for a consistent object.
profile_id = eRepublik-provided citizen (player) ID.
create_ts = when the original oid was added to db.
update_ts = when a physical row (uid) was created ("upserted").
delete_ts = when a physical row (uid) was logically deleted.
hash_id = hash of all non-audit values in a row.

Non-audit values on the user table are encrypted
at the column level. If file-level encryption is
desired, use sqlite management tool for that.
Not presently an option managed via this app.

Module:    dbase
Class:     Dbase
Author:    PQ <pq_rfw @ pm.me>
"""
import sqlite3 as sq3
from collections import namedtuple
from copy import copy
from os import path, remove
from pathlib import Path
from pprint import pprint as pp  # noqa: F401
from typing import Literal

from cipher import Cipher
from structs import Structs
from texts import Texts
from utils import Utils

UT = Utils()
TX = Texts()
CI = Cipher()
ST = Structs()


class Dbase(object):
    """Provide functions to support database setup, usage, maintenance.

    SQLite natively supports the following types:
        NULL, INTEGER, REAL, TEXT, BLOB.
    Python equivalents are:
        None, int, float, string, byte
    """

    class Types(object):
        """Define non-standard data types."""

        dbaction = Literal['add', 'upd', 'del']
        tblnames = Literal['user', 'citizen']

    def create_main_db(self):
        """Create main database."""
        db_path = path.join(UT.get_home(), TX.dbs.db_path)
        if not Path(db_path).exists():
            msg = TX.shit.f_bad_path + db_path
            raise Exception(OSError, msg)
        db_full_path = path.join(db_path, TX.dbs.db_name)
        if not Path(db_full_path).exists():
            self.create_tables(db_full_path)

    def disconnect_dmain(self):
        """Drop connection to main database at specified path."""
        if hasattr(self, "dmain_conn") and self.dmain_conn is not None:
            try:
                self.dmain_conn.close()
            except RuntimeWarning:
                pass
        self.dmain_conn = None

    def connect_dmain(self, p_main_db):
        """Open connection to main database at specified path.

        Create a db file if one does not already exist.

        Args:
            p_main_db (str): full path to main db file
        """
        self.disconnect_dmain()
        self.dmain_conn = sq3.connect(p_main_db)

    def disconnect_dbkup(self):
        """Drop connection to backup database at specified path."""
        if hasattr(self, "dbkup_conn") and self.dbkup_conn is not None:
            try:
                self.dbkup_conn.close()
            except RuntimeWarning:
                pass
        self.dbkup_conn = None

    def connect_dbkup(self, p_bkup_db):
        """Open connection to backup database at specified path.

        Args:
            p_bkup_db (str): full path to backup DB file
        """
        self.disconnect_dbkup()
        self.dbkup_conn = sq3.connect(p_bkup_db)

    def disconnect_darcv(self):
        """Drop connection to archive database at specified path."""
        if hasattr(self, "darcv_conn") and self.darcv_conn is not None:
            try:
                self.darcv_conn.close()
            except RuntimeWarning:
                pass
        self.darcv_conn = None

    def connect_darcv(self, p_arcv_db):
        """Open connection to archive database at specified path.

        Args:
            p_arcv_db (str): full path to archive DB file
        """
        self.disconnect_darcv()
        self.darcv_conn = sq3.connect(p_arcv_db)

    def get_data_keys(self, p_tbl_nm: Types.tblnames) -> list:
        """Get 'data' class column names for selected DB table.

        Args:
            p_tbl_nm (Types.tblnames): user, citizen
        Returns:
            list: of "data" dataclass column names
        """
        data_keys =\
            ST.UserFields.keys() if p_tbl_nm == 'user'\
            else ST.CitizenFields.keys()
        return data_keys

    def create_tables(self, p_db_path: str):
        """Create DB tables on main database.

        Args:
            p_db_path (str): Ful path to main DB location.

        Raises:
            Fail if cursor connection has not been established.
        """
        self.connect_dmain(p_db_path)
        cur = self.dmain_conn.cursor()
        for tbl_nm in ['user', 'citizen']:
            sql = "SELECT name FROM sqlite_master " +\
                "WHERE type='table' AND name='{}';".format(tbl_nm)
            cur.execute(sql)
            result = cur.fetchall()
            # Table does not exist...
            if len(result) == 0:
                data_keys = self.get_data_keys(tbl_nm)
                col_nms = data_keys + ST.AuditFields.keys()
                for ix, col in enumerate(col_nms):
                    if col == "encrypt_key":
                        col_nms[ix] = col + " BLOB"
                    else:
                        col_nms[ix] = col + " TEXT"
                    if col in ("oid", "uid", "create_ts", "hash_id"):
                        col_nms[ix] += " NOT NULL"
                    if col == "uid":
                        col_nms[ix] += " PRIMARY KEY"
                sql = "CREATE TABLE {}({});".format(tbl_nm, ", ".join(col_nms))
                cur.execute(sql)
        cur.close()
        self.dmain_conn.commit()
        self.disconnect_dmain()

    def backup_db(self):
        """Make full backup of the main database to the backup db.

        Create a backup database file if it does not exist, else
          overwrite existing backup DB file.
        """
        main_db = path.join(UT.get_home(), TX.dbs.db_path, TX.dbs.db_name)
        bkup_db = path.join(UT.get_home(), TX.dbs.bkup_path, TX.dbs.db_name)
        self.connect_dmain(main_db)
        self.connect_dbkup(bkup_db)
        self.dmain_conn.backup(self.dbkup_conn, pages=0, progress=None)
        self.disconnect_dmain()
        self.disconnect_dbkup()

    def archive_db(self):
        """Make full backup of main database with a timestamp.

        Distinct from regular backup file. A time-stamped, one-time copy.
        Make a point-in-time copy, e.g., prior to doing a purge.
        """
        main_db = path.join(UT.get_home(), TX.dbs.db_path, TX.dbs.db_name)
        dttm = UT.get_dttm('UTC')
        arcv_db = path.join(UT.get_home(), TX.dbs.arcv_path,
                            "{}.{}".format(TX.dbs.db_name, dttm.curr_ts))
        self.connect_dmain(main_db)
        self.connect_darcv(arcv_db)
        self.dmain_conn.backup(self.darcv_conn, pages=0, progress=None)
        self.disconnect_dmain()
        self.disconnect_darcv()

    def set_insert_sql(self,
                       p_tbl_nm: Types.tblnames,
                       p_data_rec: dict,
                       p_audit_rec: dict) -> str:
        """Format SQL for an INSERT.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, citizen
            p_data_rec (dict): mirrors a "data" dataclass
            p_audit_rec (dict): mirrors the "audit" dataclass

        Returns:
            str: formatted SQL to execute
        """
        sql_cols = list(p_data_rec.keys()) + list(p_audit_rec.keys())
        sql_cols_txt = ", ".join(sql_cols)
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
                                                        sql_cols_txt,
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
            tuple of updated dicts ("audit": .., "data": ..)
        """
        data_rec = p_data_rec
        audit_rec = p_audit_rec
        hash_str = ""
        for cnm, val in p_data_rec.items():
            if (cnm != "encrypt_key"
                    and val not in (None, "None", "")):
                hash_str += str(val)
        audit_rec["hash_id"] = UT.get_hash(hash_str)
        return(data_rec, audit_rec)

    def encrypt_data_values(self,
                            p_data: dict) -> dict:
        """Encrypt data on user table row.

        Args:
            p_data (dict): mirrors "data" dataclass

        Returns:
            dict: encrypted "data" row
        """
        data_rec = p_data
        for cnm, val in p_data.items():
            if (cnm != "encrypt_key"
                    and val not in (None, "None", "")):
                data_rec[cnm] = CI.encrypt(str(val), p_data["encrypt_key"])
        return data_rec

    def query_latest(self,
                     p_tbl_nm: Types.tblnames,
                     p_oid: str = None,
                     p_single: bool = True):
        """Get the latest non-deleted record(s) for selected table.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, citizen
            p_oid (str): Required for citizen.
            p_single (bool): If True, return only latest row even if there are
                             multiples with NULL delete_ts. If False, return
                             all latest rows that have a NULL delete_ts.

        Returns:
            dict ("data": ..., "audit", ...) for user   OR
            list (of dicts like this ^) for citizen
        """
        db_recs = None
        if p_tbl_nm == "user":
            db_recs = self.query_user(p_single)
        elif p_tbl_nm == "citizen":
            db_recs = self.query_citizen_by_oid(p_oid, p_single)
        return db_recs

    def set_insert_data(self,
                        p_tbl_nm: Types.tblnames,
                        p_data: dict) -> tuple:
        """Format one logically new row for main database.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, citizen
            p_data (dict): mirrors a "data" dataclass

        Returns:
            tuple: (dict: "data":.., dict: "audit":..)
        """
        audit_rec = dict()
        for cnm in ST.AuditFields.keys():
            audit_rec[cnm] = copy(getattr(ST.AuditFields, cnm))
        audit_rec["uid"] = UT.get_uid()
        audit_rec["oid"] = UT.get_uid()
        dttm = UT.get_dttm('UTC')
        audit_rec["create_ts"] = dttm.curr_utc
        audit_rec["update_ts"] = dttm.curr_utc
        audit_rec["delete_ts"] = None
        data_rec, audit_rec =\
            self.hash_data_values(p_data, audit_rec)
        recs = self.query_latest(p_tbl_nm, audit_rec["oid"])
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
                        p_oid: str) -> tuple:
        """Format one logically updated row to main database.

        Do nothing if no value-changes are detected.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, citizen
            p_data (dict): that mirrors a "data" dataclass
            p_oid (str): Object ID of record to be updated

        Returns:
            tuple: (dict: "data":.., dict: "audit":..,
                    hash_id of previous version) if prev row exits, else
                    (None, None, None)
        """
        recs = self.query_latest(p_tbl_nm, p_oid)
        aud = UT.make_namedtuple("aud", recs["audit"])
        dat = UT.make_namedtuple("dat", recs["data"])
        if not aud or aud.oid != p_oid:
            msg = TX.shit.f_upsert_failed
            raise Exception(ValueError, msg)
        audit_rec = UT.make_dict(ST.AuditFields.keys(), aud)
        audit_rec["uid"] = UT.get_uid()
        audit_rec['oid'] = copy(aud.oid)
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
                               p_oid: str):
        """Store non-NULL delete_ts on previously-active record.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, citizen
            p_oid (str): Object ID of record to be marked as deleted.
        """
        recs = self.query_latest(p_tbl_nm, p_oid, False)
        try:
            aud = UT.make_namedtuple("aud", recs[0]["audit"])
        except:     # noqa: E722
            aud = UT.make_namedtuple("aud", recs["audit"])
        dttm = UT.get_dttm('UTC')
        sql = "UPDATE {}".format(p_tbl_nm)
        sql += " SET delete_ts = '{}'".format(dttm.curr_utc)
        sql += " WHERE uid = '{}';".format(aud.uid)
        return sql

    def execute_txn_sql(self,
                        p_db_action: Types.dbaction,
                        p_tbl_nm: Types.tblnames,
                        p_sql: str,
                        p_oid: str = None,
                        p_encrypt_key: str = None):
        """Execute SQL to modify the database content.

        Args:
            p_db_action (Types.dbaction -> string): add, upd, del
            p_tbl_nm (Types.tblnames -> str): user, citizen
            p_sql (string): the SQL statement to execute
            p_oid (string): if updating a record, used to delete previous
            p_encrypt_key (string): if adding or updating a user record
        """
        main_db = path.join(UT.get_home(), TX.dbs.db_path, TX.dbs.db_name)
        self.connect_dmain(main_db)
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
            self.write_db("del", p_tbl_nm, None, p_oid)

    def write_db(self,
                 p_db_action: Types.dbaction,
                 p_tbl_nm: Types.tblnames,
                 p_data: dict = None,
                 p_oid: str = None):
        """Write a record to the DB.

        Args:
            p_db_action (Types.dbaction -> str): add, upd, del
            p_tbl_nm (Types.tblnames -> str): user, citizen
            p_data (dict): mirrors a "data" dataclass. None if "del".
            p_oid (string): Required for upd, del. Default is None.
        """
        if p_db_action == "add":
            data_rec, audit_rec = self.set_insert_data(p_tbl_nm, p_data)
        elif p_db_action == "upd":
            data_rec, audit_rec, prev_hash_id =\
                self.set_upsert_data(p_tbl_nm, p_data, p_oid)
        sql = ""
        encrypt_key = ""
        if p_db_action in ("add", "upd"):
            if data_rec is not None and audit_rec is not None:
                sql = self.set_insert_sql(p_tbl_nm, data_rec, audit_rec)
                encrypt_key = data_rec["encrypt_key"]\
                    if "encrypt_key" in data_rec.keys() else False
        elif p_db_action == "del":
            sql = self.set_logical_delete_sql(p_tbl_nm, p_oid)
        if sql:
            self.execute_txn_sql(p_db_action, p_tbl_nm, sql,
                                 p_oid, encrypt_key)

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
        data_keys = ST.UserFields.keys()
        data_keys.remove("encrypt_key")
        for cnm in data_keys:
            if user_data[cnm] and user_data[cnm] not in (None, "None", ""):
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
          timestamp at the end of the tuple.
        Cast each row of returned data into a namedtuple that
          mirrors a Struct DB schema dataclass. Put those in a list.
          Ignore row if it has all None values.

        This formatter assumes no derived columns. Use it only for
         "straight" queries against the database.

        Args:
            p_tbl_nm (Types.tblnames -> str): user, citizen
            p_result (sqlite result set -> list): list of tuples

        Returns:
            list: each row is dict of dicts keyed by "data", "audit",
                  mirroring appropriate dataclass DB structures
        """
        def init_recs():
            dat_rec = dict()
            aud_rec = dict()
            for cnm in dat_keys:
                dat_rec[cnm] = copy(getattr(dat_dflt, cnm))
            for cnm in aud_keys:
                aud_rec[cnm] = copy(getattr(ST.AuditFields, cnm))
            return (dat_rec, aud_rec)

        data_out = list()
        dat_keys = self.get_data_keys(p_tbl_nm)
        aud_keys = ST.AuditFields.keys()
        col_nms = dat_keys + aud_keys
        dat_dflt = ST.UserFields if p_tbl_nm == 'user'\
            else ST.CitizenFields
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

    def format_query_sql(self,
                         p_tbl_nm: Types.tblnames,
                         p_single: bool = True):
        """Format a SELECT query, with option to return only latest row.

        Returns all cols from selected table.

        Args:
            p_tbl_nm (Types.tblnames -> str)
            p_single (bool): If True, return only the latest row

        Returns:
            dict: of (dicts keyed by "data", "audit")  or
            list of dicts like that ^  or
            None if no rows found
        """
        data_cols = ST.UserFields.keys() if p_tbl_nm == "user"\
            else ST.CitizenFields.keys()
        col_nms = data_cols + ST.AuditFields.keys()
        col_nms_txt = ", ".join(col_nms)
        sql = "SELECT {}, ".format(col_nms_txt)
        if p_single:
            sql += "MAX(update_ts)"
        else:
            sql = sql[:-2]
        sql += " FROM {} ".format(p_tbl_nm)
        sql += "WHERE delete_ts IS NULL;"
        recs = self.execute_query_sql(p_tbl_nm, sql, p_single)
        return recs

    def execute_query_sql(self,
                          p_tbl_nm: Types.tblnames,
                          p_sql: str,
                          p_single: bool = True):
        """Execute a SELECT query, with option to return only latest row.

        Args:
            p_sql (str) DB SELECT to execute
            p_tbl_nm (Types.tblnames -> str)
            p_single (bool): If True, return only the latest row

        Returns:
            dict: of (dicts keyed by "data", "audit")  or
            list of dicts like that ^  or
            None if no rows found
        """
        main_db = path.join(UT.get_home(), TX.dbs.db_path, TX.dbs.db_name)
        self.connect_dmain(main_db)
        cur = self.dmain_conn.cursor()
        result = cur.execute(p_sql).fetchall()
        self.disconnect_dmain()
        data_recs = self.format_query_result(p_tbl_nm, result)
        if len(data_recs) < 1:
            data_recs = None
        elif p_single:
            data_recs = data_recs[0]
        return data_recs

    def query_user(self, p_single=True) -> dict:
        """Run read-only query against the user table.

        Args:
            p_single (bool): If True, return only the latest row

        Returns:
            dict: of (dicts keyed by "data", "audit")
        """
        return self.format_query_sql("user", p_single)

    def query_citizen_by_oid(self,
                             p_oid: str,
                             p_single: bool = True) -> dict:
        """Run read-only query against the citizen table.

        Return latest non-deleted record that matches on PID.

        Args:
            p_oid (str): efriends DB unique object ID
            p_single (bool): If True, return only latest row

        Returns:
            dict: of (dicts keyed by "data", "audit")
        """
        col_nms = list(ST.CitizenFields.keys()) +\
            list(ST.AuditFields.keys())
        col_nms_txt = ", ".join(col_nms)
        sql = "SELECT {}, ".format(col_nms_txt)
        if p_single:
            sql += " MAX(update_ts)"
        else:
            sql = sql[:-2]
        sql += " FROM citizen WHERE oid = '{}'".format(str(p_oid))
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
            dict: of (dicts keyed by "data", "audit")
        """
        col_nms = list(ST.CitizenFields.keys()) +\
            list(ST.AuditFields.keys())
        col_nms_txt = ", ".join(col_nms)
        sql = "SELECT {}, ".format(col_nms_txt)
        sql += " MAX(update_ts) FROM citizen"
        sql += " WHERE profile_id = '{}'".format(str(p_profile_id))
        sql += " AND delete_ts is NULL;"
        recs = self.execute_query_sql("citizen", sql, p_single=True)
        return recs

    def query_citizen_by_name(self,
                              p_citizen_nm: str) -> dict:
        """Run read-only query against the citizen table.

        Return latest non-deleted record that matches on citizen name.

        Args:
            p_citizen_nm (str): eRepublik citizen name

        Returns:
            dict: of (dicts keyed by "data", "audit")
        """
        col_nms = list(ST.CitizenFields.keys()) +\
            list(ST.AuditFields.keys())
        col_nms_txt = ", ".join(col_nms)
        sql = "SELECT {}, ".format(col_nms_txt)
        sql += " MAX(update_ts) FROM citizen"
        sql += " WHERE name = '{}'".format(str(p_citizen_nm))
        sql += " AND delete_ts is NULL;"
        recs = self.execute_query_sql("citizen", sql, p_single=True)
        return recs

    def query_for_profile_id_list(self) -> list:
        """Return a list of all active citizen profile IDs.

        Returns:
            list: of eRepublik citizen profile IDs
        """
        sql = "SELECT profile_id "
        sql += "FROM citizen WHERE delete_ts IS NULL;"
        recs = self.execute_query_sql("citizen", sql, p_single=False)
        id_list = list()
        for row in recs:
            id_list.append(row['data']['profile_id'])
        return id_list

    def query_citizen_sql(self, sql_file_name: str) -> list:
        """Run SQL read in from a file.

        Returns:
            list of tuples. First tuple contains headers, the rest values.
        """
        sql_file = path.join(UT.get_home(), TX.dbs.db_path, sql_file_name)
        with open(sql_file) as sqf:
            sql = sqf.read()
        sqf.close()
        main_db = path.join(UT.get_home(), TX.dbs.db_path, TX.dbs.db_name)
        self.connect_dmain(main_db)
        cur = self.dmain_conn.cursor()
        result = cur.execute(sql).fetchall()
        # Much nicer than the formatting I was doing earlier!
        headers = [meta_h[0] for meta_h in cur.description]
        self.disconnect_dmain()
        result.insert(0, tuple(headers))
        return(result)


    # ================  untested code =========================
    def destroy_all_dbs(self, db_path: str):
        """Delete all database files.

        Args:
            db_path (string): Full path to the .db file

        Returns:
            bool: True if db_path legit points to a file

        @DEV - Add logging messages
        @DEV - Destroy only specific DBs
        """
        for d_path in [path.join(UT.get_home(), TX.dbs.db_path),
                       path.join(UT.get_home(), TX.dbs.bkup_path),
                       path.join(UT.get_home(), TX.dbs.arcv_path)]:
            remove(d_path)

    def purge_rows(self, p_oids: list, p_cursor: object):
        """Physically delete a row from citizen table on main db.

        Args:
            p_oids (list): (oids, delete_ts) tuples associated
                with rows to physically delete
            cur (object): a cursor on the main database
        """
        for row in p_oids:
            d_oid = row[0]
            d_delete_ts = row[1]
            sql = "DELETE citizen WHERE uid = '{}' ".format(d_oid)
            sql += "AND delete_ts = '{}';".format(d_delete_ts)
            p_cursor.execute(sql)

    def purge_db(self):
        """Remove rows from main db citizen table."""
        self.archive_db()

        # Modify to use an appropriate purge threshold, not just
        # "deleted before today"
        dttm = UT.get_dttm()
        sql = "SELECT oid, delete_ts FROM citizen "
        sql += "WHERE delete_ts < '{}' ".format(dttm.curr_utc)
        sql += "AND delete_ts IS NOT NULL;"

        main_db = path.join(UT.get_home(), TX.dbs.db_path, TX.dbs.db_name)
        self.connect_dmain(main_db)
        cur = self.dmain_conn.cursor()
        oid_list = [row for row in cur.execute(sql)]
        self.purge_rows(cur, oid_list)
        self.dmain_conn.commit()
        self.disconnect_dmain()
