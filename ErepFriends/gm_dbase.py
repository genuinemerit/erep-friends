# noqa: E902
"""
Module:    gm_dbase
Class:     GmDbase
Author:    PQ <pq_rfw @ pm.me>

    Simple database manager for erep_friends using sqlite3
    Also handles some file management
"""
import json                             # noqa: F401
import sqlite3 as sq3
import sys
from collections import namedtuple
from os import path, remove

from pathlib import Path
from pprint import pprint as pp         # noqa: F401

from gm_reference import GmReference
from gm_functions import GmFunctions
from gm_encrypt import GmEncrypt

GR = GmReference()
GF = GmFunctions()
GE = GmEncrypt()


class GmDbase(object):
    """
    @class:  GmDbase

    Provide functions to support database setup, usage, maintenance.
    SQLite natively supports the following types:
        NULL, INTEGER, REAL, TEXT, BLOB.
    Python equivalents are:
        None, int, float, string, byte
    """
    def __init__(self):
        """ Initialize GmDbase object
        """
        pass

    def __repr__(self):
        """ Print description of class
        @DEV
            TODO when code has settled down
        """
        pass

    def __set_db_path(self) -> str:
        """ Set file URI to the configured database

        Returns:
            string: path to database as specified in config file
        """
        if not Path(self.opt.data_path).exists():
            raise Exception(IOError,
                "{} could not be reached".format(self.opt.data_path))
        db_path = path.join(self.opt.data_path, self.opt.db_name)
        return db_path

    def __set_backup_path(self) -> str:
        """ Set file URI to the backup database
            If the database is full-encrypted, the system does not attempt
               to backup a copy of the encryption key. That is up to user.
            There is a single backup database, with same name as main DB.

        Returns:
            string: path to backup database as specified in config file
        """
        if not Path(self.opt.bkup_db_path).exists():
            raise Exception(IOError,
                "{} could not be reached".format(self.opt.bkup_db_path))
        db_path = path.join(self.opt.bkup_db_path, self.opt.db_name)
        return db_path

    def __set_archive_path(self) -> str:
        """ Set file URI to the purge archive database
            The name of the archive DB gets a timestamp appended to it.
            If the database is full-encrypted, the system does not attempt
               to archive a copy of the encryption key. That is up to user.
            A new archive file is created when purge is run.
            Removing old archives is not handled. Up to the user.

        Returns:
            string: path to archive database as specified in config file
        """
        if not Path(self.opt.arcv_db_path).exists():
            raise Exception(IOError,
                            "{} could not be reached".format(arcv_dbpath))
        dttm = GF.get_dttm()
        dbnm = self.opt.db_name.split(".db")
        arcv_db_nm = dbnm[0] + "_" + dttm.curr_ts + ".db"
        db_path = path.join(self.opt.arcv_db_path, arcv_db_nm)
        return db_path

    def __validate_table_name(self, p_table_nm: GR.dbtable_t):
        """ Only allow table names that are part of the schema

        Args:
            p_table_nm (GR.dbtable_t): a valid table name (string)
        """
        if p_table_nm.lower() not in GR.DBTABLE:
            raise Exception(IOError,
                    "{} not a valid table name".format(p_table_nm))

    def __validate_filter_name(self, p_filter_nm: GR.filter_t):
        """ Only allow permitted filter (column) names

        Args:
            p_filter_nm (GR.filter_t): a valid friends col filter name (string)
        """
        if p_filter_nm.lower() not in GR.FRIEND_FILTER:
            raise Exception(IOError,
                    "Filtering on {} is not supported".format(p_filter_nm))

    def __friends_sql(self, p_filter: dict, p_sql: str) -> str:
        """ Build SQL to do read query on the friends table.
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
            p_filter (dict): of valid col-nm, value pairs
            p_sql (str): partially built SQL string

        Raises:
            Exception: IOError if mal-formed "LIST" request

        Returns:
            str: built-out logic in SQL string
        """
        sql = p_sql
        where_items = list()
        for col_nm, col_val in p_filter.items():
            self.__validate_filter_name(col_nm)
            if col_val.upper() == "LIST" and len(list(p_filter.keys())) > 1:
                raise Exception(IOError,
                        "LIST must be singleton request")
            where_items.append(" {} = '{}'".format(col_nm, col_val))
        if len(where_items) > 1:
            sql += "WHERE {}".format("AND ".join(where_items))
            sql += " AND delete_ts IS NULL;"
        else:
            col_nm = list(p_filter.keys())[0]
            sql = "SELECT {}, COUNT({}), MAX(update_ts) ".format(col_nm, col_nm)
            sql += "FROM friends WHERE delete_ts IS NULL"
            sql += " GROUP BY {};".format(col_nm)
        return sql

    def config_db(self, p_db_name: str,
                  p_data_path: str, p_bkup_db_path: str, p_arcv_db_path: str):
        """ Define DB configuration. Load values from parameters.

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

        # pp(("self.opt", self.opt))

    def disconnect_db(self):
        """ Drop connection to main database at configured path.
        """
        self.dbmain_conn.close()
        self.dbmain_conn = None

    def disconnect_dbkup(self):
        """ Drop connection to backup database at configured path.
        """
        self.dbkup_conn.close()
        self.dbkup_conn = None

    def disconnect_darcv(self):
        """ Drop connection to archive database at configured path.
        """
        self.dbarcv_conn.close()
        self.dbarcv_conn = None

    def connect_db(self):
        """ Open connection to main database at configured path.
            Sets class-level property to hold connection.
        """
        self.disconnect_db()
        db = self.__set_db_path()
        self.dbmain_conn = sq3.connect(db)

    def connect_dbkup(self):
        """ Open connection to backup database at configured path.
            Sets class-level property to hold connection.
        """
        self.disconnect_dbkup()
        dbkup = self.__set_backup_path()
        self.dbkup_conn = sq3.connect(dbkup)

    def connect_darcv(self):
        """ Open connection to archive database at configured path.
            Sets class-level property to hold connection.
        """
        self.disconnect_darcv()
        darcv = self.__set_archive_path()
        self.dbarcv_conn = sq3.connect(darcv)

    def create_tables(self, cur: object):
        """ Create DB tables for efriends database.
            - Schema defined in GR.set_structures.
            - string (TEXT) data type used for all columns
            - Only hash_id and create_ts are NOT NULL
            - uid is the only PRIMARY KEY

        Args:
            cur (object): cursor attached to a sqlite3 db connection
        """
        for tbl_nm in GR.DBTABLE:
            sql = "SELECT name FROM sqlite_master " +\
                "WHERE type='table' AND name='{}';".format(tbl_nm)
            cur.execute(sql)
            result = cur.fetchall()
            if len(result) == 0:
                fields = list(GR.DBSCHEMA[tbl_nm]._fields)
                for idx, val in enumerate(fields):
                    if val == "encrypt_key":
                        fields[idx] = val + " BLOB"
                    else:
                        fields[idx] = val + " TEXT"
                    if val in ("create_ts", "hash_id"):
                        fields[idx] += " NOT NULL"
                    if val == "uid":
                        fields[idx] += " PRIMARY KEY"
                sql_fields = ", ".join(fields)
                sql = "CREATE TABLE {}({});".format(tbl_nm, sql_fields)
                cur.execute(sql)
        cur.close()

    def backup_db(self):
        """ Make full backup of the main database to the backup db
            Create backup database file if it does not exist.

            @DEV
                Consider supporting a scheme of rolling backups.
                In other words, archive a backup before replacing it.
                Then remove oldest backups periodically.
        """
        pp(("self.opt.bkup_db_path", self.opt.bkup_db_path))

        if self.opt.bkup_db_path in (None, 'None', ""):
            print("No backup database path has been defined")
        else:
            self.connect_db()
            self.connect_dbkup()
            self.dbmain_conn.backup(self.dbkup_conn, pages=0, progress=None)
            self.disconnect_db()
            self.disconnect_dbkup()

    def archive_db(self):
        """ Make full backup of main database before purging it.
            This is distinct from the regular backup file.
            It is a time-stamped, one-time copy.
        """
        pp(("self.opt.arcv_db_path", self.opt.arcv_db_path))

        if self.opt.arcv_db_path in (None, 'None', ""):
            print("No archive database path has been defined")
        else:
            self.connect_db()
            self.connect_darcv()
            self.dbmain_conn.backup(self.dbarcv_conn, pages=0, progress=None)
            self.disconnect_db()
            self.disconnect_darcv()

    def create_db(self):
        """ Create main and backup DBs using efriends schema.
            DBs created at connection points if don't already exist.

            Not implementing the Sqlite Encryption Extension at this time.
            SQLCipher also seems like a mature solution. See:
            https://www.zetetic.net/sqlcipher/  and
            https://charlesleifer.com/blog/encrypted-sqlite-databases-with-python-and-sqlcipher/
            but it is proprietary.

            Will support encryption at the record level for an "add" action.
            If the new record is encrypted, then any subsequent "upd" delta records
            for that uid will also be encrypted.
        """
        # Create main database
        self.connect_db()
        self.create_tables(self.dbmain_conn.cursor())
        self.dbmain_conn.commit()
        self.disconnect_db()
        # Create backup database
        self.backup_db()

    def get_rec_data(self, p_tbl_nm:  GR.dbtable_t,
                     p_data_row: GR.NamedTuple) -> GR.NamedTuple:
        """Break out col names and values that are not audit fields.

        Args:
            p_tbl_nm (str): valid db table name
            p_data_row (namedtuple): full set of col names and values

        Returns:
            GR.NamedTuple: rec_data
        """
        rec_data = namedtuple("rec_data", "tbl_struct col_nms col_vals")
        rec_data.tbl_struct = GR.DBSCHEMA[p_tbl_nm]._fields
        rec_data.col_nms = [col_nm for col_nm in tbl_struct
                                    if col_nm not in GR.auto._fields]
        rec_data.col_vals =\
            [getattr(p_data_row, col_nm) for col_nm in rec_data.col_nms]
        return rec_data

    def write_db(self,
                 p_db_action: GR.dbaction_t,
                 p_tbl_nm: GR.dbtable_t,
                 p_data_row: GR.NamedTuple,
                 p_uid: str = None,
                 p_encrypt: bool = False):
        """ Write a record to the DB. It is a write-only system,
              with no physical updates or deletes except on purge.
            Update and Delete actions only accept UID as key value.
            UID and Audit fields work as follows
            - DBACTION is "add":
              - Generate a new UID
              - Compute value of hash_is using concat of all fields
                 except UID, hash_id and audit timestamps
              - Set both create_ts and update_ts to timestamp value
              - Set delete_ts to NULL
              - Write new row
            - DBACTION is "upd":
              - Read/get record = UID and
                  (update_ts is MAX or delete_ts is not NULL)
              - If delete_ts is not NULL, return failure, else:
                - Copy record, then update specified columns
                - Recompute hash value. If it is unchanged, do nothing, else:
                    - Set update_ts to timestamp value
                    - Write new row
            - DBACTION is "del":
              - Read/get record = UID and
                  (update_ts is MAX or delete_ts is not NULL)
              - If delete_ts is not NULL, do nothing, else:
                - Set delete_ts to timestamp value
            - All audit timestamps should use UTC date/time.
              - Default tz is America/Los_Angeles (UTC -8) which is
                "eRepublik Standard Time".  Use the "local" value
                returned from GR.dttm() if it needs to reflect eRep
                date/time.
            @DEV
                Somewhere I saw a little API for converting date/time into
                an eRep Day Number.  That would be a handy routine to have.

                For user table, limit them in various ways, like:
                - Only one user profile ID can be defined, but password and
                   email associated with it can be updated.
                - Encrypt tags/keys cannot be deleted if they are in use on
                  any active databases.
                - Encrypt key is generated when adding a user row
                - Why not use the hash-id as the PK? Do I really need UID?
                  -- Yeah, I guess for being able to trace changes.
        Args:
            p_db_action (string, Literal): 'add', 'upd', or 'del'
            p_tbl_nm (string, Literal): 'encrypt', 'user', or 'friends'
            p_data_row (GR.NamedTuple): using one of the GR.*_rec structure
                that matches the table name.
                A value of None in any given column indicates "no action"
                for that column.
            p_uid (string, optional): Default is None. Required if action
                is 'upd' or 'del'.
            p_encrypt_tag (string, optional): Deafult is None. If not None, then
                non-NULL data values are encrypted using key associated
                with the provided tag. Has no effect on "del" action.

        Return:
            GR.NamedTuple: A copy of the added, updated, or deleted record,
                           formatted using the GR data structures.

        @DEV
            Clean this up.
            Add update and delete logic.
            Handle a friends record
        """
        if p_db_action not in GR.DBACTION:
            raise Exception(IOEror,
                "Database action must be in {}".format(str(self.DBACTION)))
        if p_tbl_nm not in GR.DBTABLE:
            raise Exception(IOEror,
                "Database table must be in {}".format(str(self.DBTABLE)))
        if p_db_action == "del":
            print("Logical DELETE DB call not enabled yet")
            return False
        if p_db_action in ("add", "upd"):
            dttm = GF.get_dttm()
            # Identify non-auto columns
            rec_data = self.get_rec_data(p_tbl_nm, p_data_row)

            # tbl_struct = GR.DBSCHEMA[p_tbl_nm]._fields
            # col_nms = [col_nm for col_nm in tbl_struct
            #                    if col_nm not in GR.auto._fields]
            # col_vals = [getattr(p_data_row, col_nm) for col_nm in col_nms]

            # Add
            if p_db_action == "add":
                if p_tbl_nm == "user":
                    # Handle encryption
                    p_data_row.is_encrypted = "True"
                    # Store encrypt_key on user record, but never return it
                    # Always look it up and only use it internally for
                    #  encryption and decryption
                    if p_data_row.encrypt_key in (None, "None", "",
                                                  b"None", b""):
                        raise Exception(ValueError,
                                        "No encryption key provided")
                    for col_val in rec_data.col_vals:
                        col_nm =\
                            rec_data.col_nms[rec_data.col_vals.index(col_val)]
                        encrypt_val = GE.encrypt_data(col_val,
                                                      p_data_row.encrypt_key)
                        setattr(p_data_row, col_nm, encrypt_val)

                # Build SQL for an INSERT
                p_data_row.uid = GF.get_uid()
                p_data_row.hash_id = GF.hash_me("".join(rec_data.col_vals))
                p_data_row.update_ts = dttm.curr_utc
                p_data_row.delete_ts = None
                p_data_row.create_ts = dttm.curr_utc
                sql_cols = ", ".join(rec_data.tbl_struct)
                sql_vals = ""
                for col_nm in tbl_struct:
                    if col_nm == "encrypt_key":
                        sql_vals += "?, "
                    else:
                        val = getattr(p_data_row, col_nm)
                        if val == None:
                            sql_vals += "NULL, "
                        else:
                            sql_vals += "'{}', ".format(val)
                sql = "INSERT INTO {} ({}) VALUES ({});".format(p_tbl_nm,
                                                    sql_cols, sql_vals[:-2])
            # Update

            # Delete

            # Execute and commit SQL
            self.connect_db()
            cur = self.dbmain_conn.cursor()
            # pp(sql)
            if "encrypt_key" in tbl_struct:
                result = cur.execute(sql, [p_data_row.encrypt_key])
            else:
                result = cur.execute(sql)
            self.dbmain_conn.commit()
            return result

    def query_db(self,
                 p_tbl_nm: GR.dbtable_t,
                 p_filter: dict = None,
                 p_decrypt: bool = True) -> object:
        """ Run read-only queries against the main database.
            AND logic is is used when multiple colums are queried.
            No JOIN or OR logic supported.
            GROUP BY is triggered by a search value of 'LIST'.
            Assemble and run the SQL.

        Args:
            p_tbl_nm (str): A valid table name.
            p_filter (dict, optional): Required for friends. For friends:
                Using col-names from GR.FRIEND_FILTERspecify 1..n columns,
                value pairs to list. Or, single col-nm with value = "LIST".
            p_decrypt (bool, optional): If True, return decrypted data,
                else return data as-is on the database.

        Returns:
            namedtuple: either GR.user_rec or GR.friends_rec
        """
        self.__validate_table_name(p_tbl_nm)
        fields = ", ".join(GR.DBSCHEMA[p_tbl_nm]._fields)
        sql = "SELECT {}, MAX(update_ts) FROM {} ".format(fields, p_tbl_nm)
        if p_tbl_nm == "friends":
            sql = self.__friends_sql(p_filter, sql)
        elif p_tbl_nm == "user":
            sql += "WHERE delete_ts IS NULL;"
        self.connect_db()
        cur = self.dbmain_conn.cursor()
        result = cur.execute(sql)

        # count number of rows being returned

        # for row in result:
        #    for item in row:
        #       (Handle decryption)

        # design a standard results-returned package
        #  that includes a reliable row count and
        #  a collection of namedtuples using the
        #  appropriate record format.
        return result

    def delete_recs(self, p_uids: list, cur: object):
        """ Physically delete a row from friends table on main db.

        Args:
            p_uids (list): (uids, delete_ts) tuples associated
                           with rows to physically delete
            cur (object): a cursor on the main database
        """
        for row in p_uids:
            d_uid = row[0]
            d_delete_ts = row[1]
            sql = "DELETE friends WHERE uid = '{}' " +\
                  "AND delete_ts = '{}';".format(d_uid, d_delete_ts)

            # pp(sql)

            cur.execute(sql)

    def purge_db(self):
        """  Remove rows from main db friends table where delete_ts older than purge ts
        """
        self.archive_db()

        dttm = GF.get_dttm()
        sql = "SELECT uid, delete_ts FROM friends "
        sql += "WHERE delete_ts < '{}' ".format(dttm.curr_utc)
        sql += "AND delete_ts IS NOT NULL;"

        self.connect_db()
        cur = self.dbmain_conn.cursor()
        uid_list = [row for row in cur.execute(sql)]
        self.delete_recs(cur, uid_list)
        self.dbmain_conn.commit()
        self.disconnect_db()

    def destroy_db(self, db_path: str) -> bool:
        """ Delete the specified database file.
            File to be removed must match a configured DB path

        Args:
            db_path (string): Full path to the .db file

        Returns:
            bool: True if db_path legit points to a file
        """
        main_full_path = self.__set_db_path()
        bkup_full_path = self.__set_backup_path()
        arcv_full_path = self.__set_archive_path()
        arcv_path = Path(arcv_full_path).parent
        destroy_full_path = path.abspath(path.realpath(db_path))
        destroy_path = Path(destroy_dpath).parent
        if destroy_full_path in (main_full_path,
                                 bkup_full_path,
                                 arcv_full_path)\
        or destroy_path == arcv_path:
            if not Path(destroy_full_path).exists():
                raise Exception(IOError,
                        "{} could not be reached".format(destroy_dbpath))
            os.remove(destroy_dbpath)
            return True
        else:
            raise Exception(IOError,
                    "{} out of scope".format(destroy_dbpath))
        return False
