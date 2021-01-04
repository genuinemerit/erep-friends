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
        if hasattr(self, 'dmain_conn'):
            self.dmain_conn.close()
        self.dmain_conn = None

    def disconnect_dbkup(self):
        """Drop connection to backup database at configured path."""
        if hasattr(self, 'dbkup_conn'):
            self.dbkup_conn.close()
        self.dbkup_conn = None

    def disconnect_darcv(self):
        """Drop connection to archive database at configured path."""
        if hasattr(self, 'darcv_conn'):
            self.darcv_conn.close()
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
        for tbl_nm in ST.self.DBSCHEMA.keys():
            sql = "SELECT name FROM sqlite_master " +\
                "WHERE type='table' AND name='{}';".format(tbl_nm)
            cur.execute(sql)
            result = cur.fetchall()
            if len(result) == 0:
                data_cols = list(ST.DBSCHEMA[tbl_nm]["data"].field_names)
                audit_cols = list(ST.DBSCHEMA[tbl_nm]["audit"].field_names)
                cols = [*data_cols, *audit_cols]
                for col in cols:
                    ix = cols.index(col)
                    if col == "encrypt_key":
                        cols[ix] = col + " BLOB"
                    else:
                        cols[ix] = col + " TEXT"
                    if col in ("create_ts", "hash_id"):
                        cols[ix] += " NOT NULL"
                    if col == "uid":
                        cols[ix] += " PRIMARY KEY"
                sql = "CREATE TABLE {}({});".format(tbl_nm, ", ".join(cols))
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

            # pp(sql)

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

    def write_db(self,
                 p_db_action: ST.Types.t_dbaction,
                 p_tbl_nm: ST.Types.t_tblnames,
                 p_data: dict,
                 p_uid: str = None,
                 p_encrypt: bool = False) -> bool:
        """Write a record to the DB.

        It is a write-only system. No physical updates or deletes
         except on purge. Update, Delete must have a UID.
        - "add"
            - Compute UID and hash.
            - Set create_ts and update_ts to timestamp
            - Set delete_ts to NULL
            - Write new row
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
            p_db_action (string -> ST.Types.t_dbaction): add, upd, del
            p_tbl_nm (string -> ST.Types.t_tblnames): user, friends
            p_data (dict): matching ST.DBSCHEMA definitions.
              A value of None means "do nothing with this column".
            p_uid (string, optional): Required for upd, del. Default is None.
            p_encrypt (bool, optional): For friends table only. If True,
              then encrypt data fields. user table data is alwasy encrypted.
              Default is False.

        Raises:
            IOError if operation fails

        @DEV
            Clean this up.
            Add update and delete logic.
            Handle a friends record
        """
        if p_db_action == "add":
            p_data["uid"] = UT.get_uid()
            hash_vals = "".join([p_data[col] for col
                                 in ST.DBSCHEMA[p_tbl_nm]["data"].fields])
            p_data["hash_id"] = UT.get_hash(hash_vals)
            dttm = UT.get_dttm()
            p_data["update_ts"] = dttm.curr_utc
            p_data["delete_ts"] = None
            p_data["create_ts"] = dttm.curr_utc
            if p_tbl_nm == "user":
                p_data["is_encrypted"] = "True"
                p_data["encrypt_key"] = CI.set_key()
                for col in ST.DBSCHEMA[p_tbl_nm]["data"].fields:
                    p_data[col] = CI.encrypt(p_data[col],
                                             p_data["encrypt_key"])
            sql_cols = ", ".join(p_data.keys())
            sql_vals = ""
            for col, val in p_data.items():
                if col == "encrypt_key":
                    sql_vals += "?, "
                elif val is None:
                    sql_vals += "NULL, "
                else:
                    sql_vals += "'{}', ".format(val)
            sql = "INSERT INTO {} ({}) VALUES ({});".format(p_tbl_nm,
                                                            sql_cols,
                                                            sql_vals[:-2])
            self.connect_dmain()
            cur = self.dmain_conn.cursor()
            if "encrypt_key" in p_data.keys():
                result = cur.execute(sql, [p_data["encrypt_key]"]])
            else:
                result = cur.execute(sql)
            self.dmain_conn.commit()
            self.dmain_conn.disconnect()
            pp(result)
            # Parse the result. Raise an exception on failures
            # return result

    def query_friends(self,
                      p_sql: str,
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

    def query_db(self,
                 p_tbl_nm: ST.Types.t_tblnames,
                 p_filter: dict = None,
                 p_decrypt: bool = True) -> tuple:
        """Run read-only queries against the main database.

        AND logic is is used when multiple colums are queried.
        No JOIN or OR logic supported.
        GROUP BY is triggered by a search value of 'LIST'.
        Assemble and run the SQL.

        Args:
            p_tbl_nm (str -> ST.Types.t_tblnames): A valid table name.
            p_filter (dict, optional): Required for friends. For friends:
                Using col-names from ST.DBSCHEMA specify 1..n columns,
                value pairs to list. Or, single col-nm with value = "LIST".
            p_decrypt (bool, optional): If True, return decrypted data,
                else return data as-is on the database.

        Returns:
            namedtuple: either ST.user_rec or ST.friends_rec
        """
        data_cols = ", ".join(ST.DBSCHEMA[p_tbl_nm]["data"].fields)
        audit_cols = ", ".join(ST.DBSCHEMA[p_tbl_nm]["audit"].fields)
        cols = [*data_cols, *audit_cols]
        sql = "SELECT {}, MAX(update_ts) FROM {} ".format(cols, p_tbl_nm)
        if p_tbl_nm == "friends":
            sql = self.query_friends(sql)
        elif p_tbl_nm == "user":
            sql += "WHERE delete_ts IS NULL;"
        self.connect_dmain()
        cur = self.dmain_conn.cursor()

        pp(("query sql", sql))

        cur_result = cur.execute(sql)

        # Making my own namedtuple.. not sure I need to?
        outrow = namedtuple("outrow", ",".join[cols])
        outlist = list()
        rowcount = 0
        for row in cur_result:
            for val in row:
                setattr(outrow, outrow[row.index(val)], val)
            if outrow.uid is not None:
                pp(("outrow.uid", outrow.uid))
                rowcount += 1
                outlist.append(outrow)

        pp(("outlist", outlist))
        # Now decrypt if is_encrypted == 'True'
        pp(("manual rowcount", rowcount))
        return (rowcount, outlist)
