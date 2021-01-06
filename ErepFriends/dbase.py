# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Simple database manager for erep_friends using sqlite3.

Also does some file management.

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
from structs import Structs
from utils import Utils

ST = Structs()
UT = Utils()
CI = Cipher()


class Dbase(object):
    """Provide functions to support database setup, usage, maintenance.

    SQLite natively supports the following types:
        NULL, INTEGER, REAL, TEXT, BLOB.
    Python equivalents are:
        None, int, float, string, byte
    """

    def config_db(self, p_db_name: str,
                  p_data_path: str,
                  p_bkup_db_path: str,
                  p_arcv_db_path: str):
        """Define DB configuration. Load values from parameters.

        Args:
            p_db_name (string): name of main application db
            p_data_path (string): full parent path to main db
            p_bkup_db_path (string): full parent path to backup db
            p_arcv_db_path (string): full parent path to archive db
        """
        self.opt =\
            namedtuple('opt', "db_name data_path bkup_db_path arcv_db_path")
        self.opt.db_name = p_db_name
        self.opt.data_path = p_data_path
        self.opt.bkup_db_path = p_bkup_db_path
        self.opt.arcv_db_path = p_arcv_db_path

    def set_dmain_path(self) -> str:
        """Set file URI to the configured database.

        Returns:
            string: path to database as specified in config file
        """
        if not Path(self.opt.data_path).exists():
            msg = "{} could not be reached".format(self.opt.data_path)
            raise Exception(IOError, msg)
        db_path = path.join(self.opt.data_path, self.opt.db_name)
        return db_path

    def set_dbkup_path(self) -> str:
        """Set file URI to the backup database.

        There is a single backup database, with same name as main DB.

        Returns:
            string: path to backup database as specified in config file
        """
        if not Path(self.opt.bkup_db_path).exists():
            msg = "{} could not be reached".format(self.opt.bkup_db_path)
            raise Exception(IOError, msg)
        db_path = path.join(self.opt.bkup_db_path, self.opt.db_name)
        return db_path

    def set_darcv_path(self) -> str:
        """Set file URI to the purge archive database.

        The name of the archive DB gets a timestamp appended to it.
        A new archive file is created when purge is run.

        Returns:
            string: path to archive database as specified in config file
        """
        if not Path(self.opt.arcv_db_path).exists():
            msg = "{} could not be reached".format(self.opt.arcv_db_path)
            raise Exception(IOError, msg)
        dttm = UT.get_dttm()
        dbnm = self.opt.db_name.split(".db")
        arcv_db_nm = dbnm[0] + "_" + dttm.curr_ts + ".db"
        db_path = path.join(self.opt.arcv_db_path, arcv_db_nm)
        return db_path

    def disconnect_dmain(self):
        """Drop connection to main database at configured path."""
        if hasattr(self, "dmain_conn") and self.dmain_conn is not None:
            try:
                self.dmain_conn.close()
            except RuntimeWarning:
                pass
        self.dmain_conn = None

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

    def connect_dmain(self):
        """Open connection to main database at configured path."""
        self.disconnect_dmain()
        db = self.set_dmain_path()
        self.dmain_conn = sq3.connect(db)

    def connect_dbkup(self):
        """Open connection to backup database at configured path."""
        self.disconnect_dbkup()
        dbkup = self.set_dbkup_path()
        self.dbkup_conn = sq3.connect(dbkup)

    def connect_darcv(self):
        """Open connection to archive database at configured path."""
        self.disconnect_darcv()
        darcv = self.set_darcv_path()
        self.darcv_conn = sq3.connect(darcv)

    def create_tables(self, cur: object):
        """Create DB tables for efriends database.

        Args:
            cur (object): cursor attached to a sqlite3 db connection
        """
        for tbl_nm in list(ST.DBSCHEMA.keys()):
            sql = "SELECT name FROM sqlite_master " +\
                "WHERE type='table' AND name='{}';".format(tbl_nm)
            cur.execute(sql)
            result = cur.fetchall()
            if len(result) == 0:
                col_nms = [*ST.FIELDS[tbl_nm], *ST.FIELDS["audit"]]
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

    def create_db(self):
        """Create main and backup DBs using efriends schema.

        Create DBs at connection points if they don't already exist.
        """
        self.connect_dmain()
        self.create_tables(self.dmain_conn.cursor())
        self.dmain_conn.commit()
        self.disconnect_dmain()
        self.backup_db()

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

    def get_schema(self, p_tbl_nm) -> tuple:
        """Pull column names and dataclass for audit and data.

        Returns:
            tuple (audit colnms, audit dataclass,
                   table data colnms, data dataclass)
        """
        a_fields = ST.FIELDS["audit"]
        aud_cols = ST.DBSCHEMA[p_tbl_nm]["audit"]
        d_fields = ST.FIELDS[p_tbl_nm]
        data_cols = ST.DBSCHEMA[p_tbl_nm]["data"]
        return(a_fields, aud_cols, d_fields, data_cols)

    def set_data_cols(self, p_tbl_nm, d_fields, data_cols,
                      aud_cols, p_data,
                      encrypt_all, encrypt_key) -> tuple:
        """Set "data" values and hash_id. Encrypt if requested.

        Returns:
            tuple (updated audit dataclass,
                   updated data dataclass)
        """
        hash_str = ""
        if p_tbl_nm == "user":
            data_cols.encrypt_key = encrypt_key
        if str(encrypt_all) == "True":
            aud_cols.is_encrypted = "True"
        hash_flds = (cnm for cnm in d_fields if cnm != "encrypt_key")
        for cnm in hash_flds:
            # set local data class to values passed in as param
            setattr(data_cols, cnm, getattr(p_data, cnm))
            val = str(getattr(data_cols, cnm))
            if val not in (None, "None", ""):        # then hash
                hash_str += val
                if aud_cols.is_encrypted == "True":  # and encrypt
                    encrypt_val = CI.encrypt(val, encrypt_key)
                    setattr(data_cols, cnm, encrypt_val)
        aud_cols.hash_id = UT.get_hash(hash_str)
        return(data_cols, aud_cols)

    def set_insert_sql(self, p_tbl_nm, d_fields, a_fields,
                       data_cols, aud_cols) -> str:
        """Format SQL for an INSERT.

        Returns:
            str: the formatted SQL to execute
        """
        sql_cols = ", ".join([*d_fields, *a_fields])
        sql_vals = ""
        for cnm in d_fields:
            val = getattr(data_cols, cnm)
            if cnm == "encrypt_key":
                sql_vals += "?, "
            elif val is None:
                sql_vals += "NULL, "
            else:
                sql_vals += "'{}', ".format(val)
        for cnm in a_fields:
            val = getattr(aud_cols, cnm)
            if val is None:
                sql_vals += "NULL, "
            else:
                sql_vals += "'{}', ".format(val)
        sql = "INSERT INTO {} ({}) VALUES ({});".format(p_tbl_nm,
                                                        sql_cols,
                                                        sql_vals[:-2])
        return(sql)

    def insert_db(self, p_db_action, p_tbl_nm, p_data,
                  p_uid, p_encrypt) -> tuple:
        """Insert one row to main database.

        add logic
        - Compute UID and hash.
        - Encrypt "data" values if requested.
        - Set create_ts and update_ts to timestamp.
        - Set delete_ts to NULL.
        - Write new row.

        Returns:
            tuple: (data field names list, "data" dataclass, sql to execute)
        """
        a_fields, aud_cols, d_fields, data_cols = self.get_schema(p_tbl_nm)
        aud_cols.uid = UT.get_uid()
        dttm = UT.get_dttm('UTC')
        aud_cols.create_ts = dttm.curr_utc
        aud_cols.update_ts = dttm.curr_utc
        aud_cols.delete_ts = None
        if p_encrypt:
            aud_cols.is_encrypted = "True"
            if p_tbl_nm == "user":
                encrypt_key = CI.set_key()
                encrypt_all = data_cols.encrypt_all
            else:
                u_list = self.query_user()
                encrypt_key = u_list[0]["data"].encrypt_key
                encrypt_all = u_list[0]["data"].encrypt_all
        data_cols, aud_cols = self.set_data_cols(p_tbl_nm, d_fields,
                                                 data_cols, aud_cols, p_data,
                                                 encrypt_all, encrypt_key)
        sql = self.set_insert_sql(p_tbl_nm, d_fields, a_fields,
                                  data_cols, aud_cols)
        return(d_fields, data_cols, sql)

    def write_db(self,
                 p_db_action: ST.Types.t_dbaction,
                 p_tbl_nm: ST.Types.t_tblnames,
                 p_data: object,
                 p_uid: str = None,
                 p_encrypt: bool = False):
        """Write a record to the DB.

        It is a write-only system. No physical updates or deletes
         except on purge. Update, Delete must have a UID.
        - "upd":
            - Read/get record = UID where update_ts is MAX
            - If delete_ts is not NULL, return failure
            - Copy record. Update specified columns.
            - Recompute hash. If unchanged, do nothing.
            - Else:
                - Set update_ts to timestamp
                - Write new row
        - "del":
            - Read/get record = UID where update_ts is MAX
            - If delete_ts is not NULL, do nothing.
            - Else:
                - Set delete_ts to timestamp
        Args:
            p_db_action (ST.Types.t_dbaction -> str): add, upd, del
            p_tbl_nm (ST.Types.t_tblnames -> str): user, friends
            p_data (object): "data" dataclass
            p_uid (string, optional): Required for upd, del. Default is None.
            p_encrypt (bool, optional): For friends only. If True, encrypt
              "data" fields. user "data" always encrypted. Default is False.
        """
        if p_db_action == "add":
            d_fields, data_cols, sql =\
                self.insert_db(p_db_action, p_tbl_nm, p_data, p_uid, p_encrypt)

        self.connect_dmain()
        cur = self.dmain_conn.cursor()
        if "encrypt_key" in d_fields:
            try:
                cur.execute(sql, [data_cols.encrypt_key])
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

    def decrypt_query_result(self, p_tbl_nm: str,
                             p_out_list: list) -> list:
        """If data is encrypted, unencrypt it.

        Args:
            p_tbl_nm (str): user or friends
            p_out_list (list): unencrypted list of dataclass results

        Returns:
            list: encrypted list of dataclass-formatted results
        """
        o_list = p_out_list
        if p_tbl_nm == "friends":
            u_list = self.query_user()
            encrypt_key = u_list[0]["data"].encrypt_key
        else:
            encrypt_key = o_list[0]["data"].encrypt_key
        col_nms = (cnm for cnm in ST.FIELDS[p_tbl_nm] if cnm != "encrypt_key")
        ix = 0
        for row in o_list:
            e_row = row
            for cnm in col_nms:
                encrypted_val = getattr(e_row["data"], cnm)
                decrypt_val = CI.decrypt(encrypted_val, encrypt_key)
                setattr(e_row["data"], cnm, decrypt_val)
                o_list[ix] = e_row
            ix += 1
        return(o_list)

    def format_query_result(self, p_tbl_nm: str,
                            p_decrypt: bool,
                            p_col_nms: list,
                            p_result: list) -> list:
        """Convert sqlite3 results into local format.

        Sqlite returns each row as a tuple in a list.
        When no rows are found, sqlite return a tuple with
          all values set to None, which is a bit odd since then
          you get a rowcount > 0.
        It does not return a named tuple or dict.
        To facilitate data management on the return side,
          cast each row into a dataclass and put those in list,
          ignoring the row if it is all None values.

        Args:
            p_tbl_nm (str): user or friends
            p_decrypt (bool): True if results should be decrypted
            p_col_nms (list): list of all col names on the row
            p_result (sqlite result set -> list): list of tuple

        Returns:
            list: each row is formatted like ST.DBSCHEMA
        """
        o_list = list()
        for row in p_result:
            o_row = ST.DBSCHEMA[p_tbl_nm]
            all_none = True
            for val in row:
                all_none = False if val is not None else all_none
                col_ix = row.index(val)
                col_nm = p_col_nms[col_ix]
                if col_nm in ST.FIELDS[p_tbl_nm]:
                    setattr(o_row["data"], col_nm, val)
                else:
                    setattr(o_row["audit"], col_nm, val)
            if not all_none:
                o_list.append(o_row)
        if p_decrypt and o_row["audit"].is_encrypted == 'True':
            o_list = self.decrypt_query_result(p_tbl_nm, o_list)
        return o_list

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
                Using col-names from ST.DBSCHEMA, specify 1..n columns and
                paired values. Or, single col-nm with value = "LIST".

        Returns:
            list: of dataclass objects containing query results  or  empty
        """
        col_nms = [*ST.FIELDS["friends"], *ST.FIELDS["audit"]]
        sql = "SELECT {}, MAX(update_ts) FROM {} ".format(", ".join(col_nms),
                                                          "friends")
        sql = self.query_friends_more(sql)
        self.connect_dmain()
        cur = self.dmain_conn.cursor()
        cur_result = cur.execute(sql).fetchall()
        o_list = self.format_query_result("friends", p_decrypt,
                                          col_nms, cur_result)
        return o_list

    def query_user(self, p_decrypt: bool = True) -> list:
        """Run read-only queries against the user table.

        Args:
            p_decrypt (bool, optional): If True, return decrypted data,
                else return data as-is on the database.

        Returns:
            list: of dataclass objects containing query results  or  empty
        """
        col_nms = [*ST.FIELDS["user"], *ST.FIELDS["audit"]]
        sql = "SELECT {}, MAX(update_ts) FROM {} ".format(", ".join(col_nms),
                                                          "user")
        sql += "WHERE delete_ts IS NULL;"
        self.connect_dmain()
        cur = self.dmain_conn.cursor()
        cur_result = cur.execute(sql).fetchall()
        o_list = self.format_query_result("user", p_decrypt,
                                          col_nms, cur_result)
        return o_list
