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
-- Categorize:
--   ? time ? geography ? relationships ?
-- Enumerate / standardize:
--   Convert geo and org data to numbers
--   Use profile IDs rather than names
-- Explore/Experiment
--   Try various visualization styles
--   Try various visualization tools
-- Apply Algorithms
--   Standard distributions
--   Time-series, changes
--   Predictive models
-- Iterate/Review/Improve
--   Publish, collect feedback
-- Distribute, optimize
--   Schedule, push
--   Collect bug reports
"""
import csv
import json
from os import path
from pathlib import Path
from pprint import pprint as pp  # noqa: F401

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
        self.sql_files = {
            "q0100": "q0100_country_party_count.sql"
        }

    def verify_sql_file(self, p_sql_nm: str) -> bool:
        """Verify SQL file exists and is valid.

        @DEV - May want to store SQL hash in DB rather than file

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
        result_dict["export"] =\
            path.join(UT.get_home(), TX.dbs.cache_path,
                      self.sql_files[p_sql_nm]).replace(".sql", "")
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

    def export_to_json(self, p_result: dict) -> str:
        """Export query results in a simple JSON format.

        Args:
            p_result (dict): as created by get_query_result()

        Returns:
            str: full path to the JSON file
        """
        export_path = p_result["export"] + ".json"
        data = list()
        for row_d in p_result["data"]:
            row_j = dict()
            for cx, val in enumerate(list(row_d)):
                col_nm = p_result["header"][cx]
                row_j[col_nm] = val
            data.append(row_j)
            with open(export_path, 'w') as jf:
                jf.write(json.dumps(data))
            jf.close()
        return export_path

    def export_to_csv(self, p_result: dict) -> str:
        """Export query results to CSV format.

        Args:
            p_result (dict): as created by get_query_result()

        Returns:
            str: full path to the CSV file
        """
        export_path = p_result["export"] + ".csv"
        with open(export_path, 'w') as cf:
            writer = csv.writer(cf, delimiter=",", quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)
            writer.writerow(list(p_result["header"]))
            for data_t in p_result["data"]:
                data_r = list(data_t)
                writer.writerow(data_r)
        cf.close()
        return export_path

    def export_to_html(self, p_result: dict,
                       p_dataframe: object) -> str:
        """Export query results to HTML format.

        Args:
            p_result (dict): as created by get_query_result()
            p_dataframe (object): Pandas df based on CSV data

        Returns:
            str: full path to the HTML file

        @DEV - FYI, pandas can also write directly to a sqlite DB using...
        data.to_sql('table-nm', '<db-connection>', ...)
        See: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_sql.html  # noqa: E501
        Parquet, hdf5 and other formats also supported
        """
        export_path = p_result["export"] + ".html"
        with open(export_path, 'w') as hf:
            hf.write(p_dataframe.to_html())
        hf.close()
        return export_path

    def export_to_df_pickle(self, p_result: dict,
                            p_dataframe: object) -> str:
        """Export query results to pickled (binary) dataframe object.

        Args:
            p_result (dict): as created by get_query_result()
            p_dataframe (object): Pandas df based on CSV data

        Returns:
            str: full path to the PKL file
        """
        export_path = p_result["export"] + ".pkl"
        p_dataframe.to_pickle(export_path)
        return export_path

    def export_to_pdf(self, p_result: dict,
                      p_html_path: str) -> str:
        """Export query results (from HTML export) to PDF file.

        Args:
            p_result (dict): as created by get_query_result()
            p_html_path (str): HTML file created for current dataset

        Returns:
            str: full path to the PDF file

        @DEV - For more about creating PDFs, see:
        - https://realpython.com/creating-modifying-pdf/#creating-a-pdf-file-from-scratch        # noqa: E501
        - https://www.reportlab.com/software/opensource/rl-toolkit/
        - https://pypi.org/project/pdfrw/#writing-pdfs
        - https://www.adobe.com/content/dam/acom/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf    # noqa: E501
        My examples, notes on PDF in ..projects/snips/Viz_and_Analytics_Playground.ipynb         # noqa: E501
        """
        export_path = p_result["export"] + ".pdf"
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
        pdfkit.from_file(p_html_path, export_path, options=options)
        return export_path

    def run_citizen_viz(self,
                        p_sql_nm: str,
                        p_file_types: list) -> dict:
        """Execute database query, format and deliver results.

        Args:
            p_sql_nm (str): ID of SQL query, like "q0100"
            p_file_types (list): one or more output file formats

        Returns:
            exports (dict): zero to many of file_type: file_location

        @DEV - use `from io import StringIO` to create an in-mem "file".
         Or use /dev/shm to write temp files, then save to disk if requested.

        @DEV - Put together some more SQL's. Include descriptions that
         can be used in the GUI? Need a process to auto-set the hash_id's on
         new SQL's.

        @DEV - See Jupyter notebook stuff on generating plots. See about
         specifying pre-fabbed visualizations for a given dataset, perhaps
         named by ID similar to the SQL id's.  See about providing generic
         plotting/diagramming for (some?) datasets.
        """
        exports = dict()
        if self.verify_sql_file(p_sql_nm):
            result = self.get_query_result(p_sql_nm)
            if "json" in p_file_types:
                exports["json"] = self.export_to_json(result)
            if "csv" in p_file_types or "html" in p_file_types or\
               "pdf" in p_file_types or "df" in p_file_types:
                csv_path = self.export_to_csv(result)
                data_df = pd.read_csv(csv_path)
            if "csv" in p_file_types:
                exports["csv"] = csv_path
            if "html" or "pdf" in p_file_types:
                html_path = self.export_to_html(result, data_df)
            if "html" in p_file_types:
                exports["html"] = html_path
            if "df" in p_file_types:
                exports["df"] = self.export_to_df_pickle(result, data_df)
            if "pdf" in p_file_types:
                exports["pdf"] = self.export_to_pdf(result, html_path)
        return(exports)
