# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Handle publishing and distributing reports and visualizatons.

Module:    reports.py
Class:     Reports/0  inherits object
Author:    PQ <pq_rfw @ pm.me>

-- Collect:
--   Get headers with data
-- Clean:
--   Trim spaces
--   Convert None to text value
--   Remove or identify dups
-- Categorize:
--   ? time ? geography ? relationships ?
-- Enumerate / standardize:
--   Convert data to numbers
--   Use profile IDs rather than names
-- Explore/Experiment
--   Try various visualization styles
--   Try various visualization tools
-- Apply Algorithms / Build Models
--   Select goodness of fit criteria
--   Select significance levels
--   Fit predictors/remove predictors
--   Standard distributions
--   Set selection & elimination rules
--   Evaluate time-series, changes
--   Evaluate predictive models
-- Iterate/Review/Improve
--   Publish, collect feedback
-- Distribute, optimize
--   Schedule, push
--   Collect bug reports

To assign hash to a SQL, select only the SQL code, then
at command line (in ../efriends), do like...:

`>>> from utils import Utils
>>> UT = Utils()
>>> sql = \"\"\"
... SELECT COUNT(name) AS Citizens,
...        citizenship_country AS Country
...   FROM citizen
...  WHERE delete_ts IS NULL and is_alive = "True"
...  GROUP BY country
...  ORDER BY citizens DESC, country ASC;
... \"\"\"
>>> print(UT.get_hash(sql.strip()))
36985b5737273dbd58386436bcfc8eb4c58b2b77682456f4935dc512925c3f3a`

and then paste in the hash after two dashes and space on line 1 of SQL.

Save as to ~/.efriends/db with a name that starts with a unique sql_id and
ends with ."sql".

If done properly, then query should show up on "viz" frame.
"""
import csv
import json
from os import listdir, path
from pathlib import Path
from pprint import pprint as pp  # noqa: F401
import shutil

import pandas as pd
import pdfkit

from dbase import Dbase
from texts import Texts
from utils import Utils

DB = Dbase()
TX = Texts()
UT = Utils()


class Reports(object):
    """Export formatter for efriends."""

    def __init__(self):
        """Initialize Reports object."""
        self.temp_path = "/dev/shm"
        self.db_path = path.join(UT.get_home(), TX.dbs.db_path)
        self.cache_path = path.join(UT.get_home(), TX.dbs.cache_path)
        self.file_types = ["json", "csv", "html", "pdf", "df"]
        self.sql_files = self.get_sql_files()

    def get_sql_files(self) -> dict:
        """Assemble dictionary of SQL files stored in DB dir.

        Returns:
            dict: {<sql_id>: <name of sql file>}
        """
        sql_files = dict()
        db_files = listdir(self.db_path)
        for dbf in db_files:
            if dbf[-4:] == ".sql":
                sql_id = dbf.split("_")[0]
                sql_files[sql_id] = dbf
        return sql_files

    def get_query_desc(self, p_sql_nm: str) -> str:
        """Return the description fro selected SQL id.

        Args:
            p_sql_nm (str): A valid sql file identifier.

        Returns:
            str: Embedded desription on line 3 of SQL file.
        """
        sqlexp_path = path.join(UT.get_home(), TX.dbs.db_path,
                                self.sql_files[p_sql_nm])
        with open(sqlexp_path) as sqf:
            _ = sqf.readline()
            _ = sqf.readline()
            sql_desc = sqf.readline()
        sqf.close()
        return sql_desc[3:].strip()

    def verify_sql_file(self, p_sql_nm: str) -> bool:
        """Verify SQL file exists and is valid.

        Args:
            p_sql_nm (str): A valid sql file identifier.

        Returns:
            bool: True if found and verified, else False.
        """
        if p_sql_nm not in self.sql_files.keys():
            return False
        sqlexp_path = path.join(UT.get_home(), TX.dbs.db_path,
                                self.sql_files[p_sql_nm])
        if not Path(sqlexp_path).exists():
            return False
        with open(sqlexp_path) as sqf:
            hash_id = sqf.readline()
            sql_id = sqf.readline()
            sql_desc = sqf.readline()
            sql = sqf.read()
        sqf.close()
        if p_sql_nm not in sql_id:
            return False
        sql = sql.strip()
        sql_hash = UT.get_hash(sql)
        if sql_hash not in hash_id:
            return False
        sql = sql.lower()
        for forbid in ("delete ", "insert ", "update ", "drop ", "create "):
            if forbid in sql:
                return False
        return True

    def get_query_result(self, p_sql_nm: str) -> dict:
        """Call database class to execute query.

        Prepare results, including some minor cleaning.
        May eventually want to move cleaning to separate functions.

        Args:
            p_sql_nm (str): A valid sql file identifier.

        Returns:
            dict: {"export": (str) path and generic export file name,
                   "header": (tuple containing col names),
                   "data" : [list containing (tuples of values)]}
        """
        result_dict = dict()
        result_dict["export"] = self.sql_files[p_sql_nm].replace(".sql", "")
        result = DB.query_citizen_sql(self.sql_files[p_sql_nm])
        result_dict["header"] = result.pop(0)
        result_dict["data"] = list()
        for row_in_t in result:
            row_out = list()
            for item in row_in_t:
                if item is None:
                    row_out.append("None")
                else:
                    row_out.append(str(item).strip())
            result_dict["data"].append(tuple(row_out))
        return result_dict

    def create_json(self, p_result: dict) -> str:
        """Put query results into a simple JSON format.

        Args:
            p_result (dict): as created by get_query_result()

        Returns:
            str: full path to the JSON temp file
        """
        file_path = path.join(self.temp_path,
                              p_result["export"] + ".json")
        data = list()
        for row_d in p_result["data"]:
            row_j = dict()
            for cx, val in enumerate(list(row_d)):
                col_nm = p_result["header"][cx]
                row_j[col_nm] = val
            data.append(row_j)
        with open(file_path, 'w') as jf:
            jf.write(json.dumps(data))
        jf.close()
        return file_path

    def create_csv(self, p_result: dict):
        """Put query results into CSV format.

        Args:
            p_result (dict): as created by get_query_result()

        Returns:
            str: full path to the CSV temp file
        """
        file_path = path.join(self.temp_path, p_result["export"] + ".csv")
        with open(file_path, 'w') as cf:
            writer = csv.writer(cf, delimiter=",", quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)
            writer.writerow(list(p_result["header"]))
            for data_t in p_result["data"]:
                data_r = list(data_t)
                writer.writerow(data_r)
        cf.close()
        return file_path

    def create_html(self, p_result: dict,
                    p_dataframe: object) -> str:
        """Put query results into HTML format.

        Args:
            p_result (dict): as created by get_query_result()
            p_dataframe (object): Pandas df based on CSV data

        Returns:
            str: full path to the HTML temp file
        """
        file_path = path.join(self.temp_path, p_result["export"] + ".html")
        with open(file_path, 'w') as hf:
            hf.write(p_dataframe.to_html())
        hf.close()
        return file_path

    def create_df_pickle(self, p_result: dict,
                         p_dataframe: object) -> str:
        """Put query results to pickled (binary) dataframe object.

        Args:
            p_result (dict): as created by get_query_result()
            p_dataframe (object): Pandas df based on CSV data

        Returns:
            str: full path to the PKL temp file
        """
        file_path = path.join(self.temp_path, p_result["export"] + ".pkl")
        p_dataframe.to_pickle(file_path)
        return file_path

    def create_pdf(self, p_result: dict,
                   p_html_file: str) -> str:
        """Put query results (from HTML export) into PDF file.

        Args:
            p_result (dict): as created by get_query_result()
            p_html_file (str): HTML file created for current dataset

        Returns:
            str: full path to the PDF temp file

        @DEV - For more about creating PDFs, see:
        - https://realpython.com/creating-modifying-pdf/#creating-a-pdf-file-from-scratch        # noqa: E501
        - https://www.reportlab.com/software/opensource/rl-toolkit/
        - https://pypi.org/project/pdfrw/#writing-pdfs
        - https://www.adobe.com/content/dam/acom/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf    # noqa: E501
        My examples, notes on PDF in ..projects/snips/Viz_and_Analytics_Playground.ipynb         # noqa: E501
        """
        file_path = path.join(self.temp_path, p_result["export"] + ".pdf")
        options = {
            'page-size': 'Letter',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ]}
        pdfkit.from_file(p_html_file, file_path, options=options)
        return file_path

    def run_citizen_viz(self,
                        p_sql_nm: str,
                        p_file_types: list) -> dict:
        """Execute database query, format and deliver results.

        Args:
            p_sql_nm (str): ID of SQL query, like "q0100"
            p_file_types (list): one or more output file formats

        Returns:
            exports (dict): zero to many of file_type: file_location
        """
        exports = dict()
        t_file = dict()
        if self.verify_sql_file(p_sql_nm):
            result = self.get_query_result(p_sql_nm)
            # Create temp files as needed
            if "json" in p_file_types:
                t_file["json"] = self.create_json(result)
            if "csv" in p_file_types or "html" in p_file_types or\
               "pdf" in p_file_types or "df" in p_file_types:
                t_file["csv"] = self.create_csv(result)
                data_df = pd.read_csv(t_file["csv"])
            if "html" in p_file_types or "pdf" in p_file_types:
                t_file["html"] = self.create_html(result, data_df)
            if "df" in p_file_types:
                t_file["pkl"] = self.create_df_pickle(result, data_df)
            if "pdf" in p_file_types:
                t_file["pdf"] = self.create_pdf(result, t_file["html"])
            # Export files
            for ftyp in p_file_types:
                ftyp = "pkl" if ftyp == "df" else ftyp
                cache_file = path.join(self.cache_path,
                                       result["export"] + "." + ftyp)
                exports[ftyp] = cache_file
                shutil.copy(t_file[ftyp], cache_file)
        return(exports)
