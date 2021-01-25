# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Manage eRepFriends app data and rules.

Module:    controls.py
Class:     Controls/0  inherits object
Author:    PQ <pq_rfw @ pm.me>
"""
import json
import sys
import time
from collections import namedtuple
from copy import copy
from os import path
from pathlib import Path
from pprint import pprint as pp  # noqa: F401

import requests

from dbase import Dbase
from logger import Logger
from structs import Structs
from utils import Utils

UT = Utils()
ST = Structs()
DB = Dbase(ST)


class Controls(object):
    """Rules engine for eRepublik."""

    def __init__(self):
        """Initialize Controls() object."""
        self.logme = False

    def check_python_version(self):
        """Validate Python version."""
        if sys.version_info[:2] < (3, 6):
            msg = "Python 3 is required.\n"
            msg += "Your version is v{}.{}.{}".format(*sys.version_info)
            raise Exception(EnvironmentError, msg)

    def set_erep_headers(self):
        """Set request headers for eRepublik calls."""
        self.erep_csrf_token = None
        self.erep_rqst = requests.Session()
        self.erep_rqst.headers = None
        self.erep_rqst.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',   # noqa: E501
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/31.0.1650.63 Chrome/31.0.1650.63 Safari/537.36'}  # noqa: E501

    def configure_database(self):
        """Instantiate Dbase object.

        Create main DB file and tables if needed.
        """
        DB.config_main_db()
        if not Path(ST.ConfigFields.main_db).exists():
            DB.create_tables()
            txt_rec = dict()
            for cnm in ST.TextFields.keys():
                txt_rec[cnm] = copy(getattr(ST.TextFields, cnm))
            DB.write_db('add', 'texts', txt_rec)
            cfg_rec = dict()
            for cnm in ST.ConfigFields.keys():
                cfg_rec[cnm] = copy(getattr(ST.ConfigFields, cnm))
            DB.write_db('add', 'config', cfg_rec)
        return ST

    def convert_data_record(self,
                            p_data_rows: dict) -> tuple:
        """Convert dicts to named tuples. Or False if no data.

        Args:
            p_data_rows (dict): with "data" and "audit" dicts

        Returns:
            tuple:  (None, None) if no results, else
                    (aud, dat) namedtuples
                        that mirror relevant dataclasses/tables
        """
        if p_data_rows is None or len(p_data_rows) < 1:
            return (None, None)
        else:
            dat = UT.make_namedtuple("dat", p_data_rows["data"])
            aud = UT.make_namedtuple("aud", p_data_rows["audit"])
            return (dat, aud)

    def get_text_data(self):
        """Query data base for most current texts record."""
        return self.convert_data_record(
            DB.query_texts())

    def get_config_data(self):
        """Query data base for most current config record."""
        return self.convert_data_record(
            DB.query_config())

    def get_database_user_data(self):
        """Query data base for most current user record, decrypted."""
        return self.convert_data_record(
            DB.query_user())

    def get_citizen_data_by_id(self, p_profile_id: str):
        """Query data base for most current citizen record."""
        return self.convert_data_record(
            DB.query_citizen_by_profile_id(p_profile_id))

    def enable_logging(self):
        """Assign log file location. Instantiate Logger object."""
        cfd, _ = self.get_config_data()
        self.logme = False
        if (cfd.log_level not in (None, "None")
                and cfd.log_level != ST.LogLevel.NOTSET):
            self.logme = True
            log_file = path.join(cfd.log_path, cfd.log_name)
            self.LOG = Logger(log_file, cfd.log_level)
            self.LOG.set_log()
            msg = "Log file location: {}".format(log_file)
            self.LOG.write_log(ST.LogLevel.INFO, msg)
            msg = "Log level: {}".format(cfd.log_level)
            self.LOG.write_log(ST.LogLevel.INFO, msg)

    def configure_log(self,
                      p_log_path: str,
                      p_log_level: str):
        """Update configs and options with path to log file and log level.

        Args:
            p_log_path (string) path to parent dir of log file
            p_log_level (string) valid key to ST.LogLevel

        Returns:
            bool: True if logging successfully turned on, else False
        """
        self.logme = False
        cfd, cfa = self.get_config_data()
        if p_log_path and p_log_path not in (None, "None"):
            log_path = p_log_path if p_log_path != cfd.log_path\
                else cfd.log_path
        if p_log_level and p_log_level not in (None, "None"):
            log_level = p_log_level if p_log_level != cfd.log_level\
                else cfd.log_level
        log_path = path.abspath(path.realpath(log_path))
        if not Path(log_path).exists():
            msg = "Log file path does not exist." +\
                "\nUser must create directory or pick a valid one."
            raise Exception(IOError, msg)
        if log_level not in ST.LogLevel.keys():
            msg = "Log level must be one of: " + str(ST.LogLevel.keys)
            raise Exception(ValueError, msg)
        data_rec = dict()
        for cnm in ST.ConfigFields.keys():
            if cnm == "log_path":
                data_rec[cnm] = log_path
            elif cnm == "log_level":
                data_rec[cnm] = log_level
            else:
                data_rec[cnm] = copy(getattr(cfd, cnm))
        DB.write_db('upd', 'config', data_rec, cfa.pid)
        self.enable_logging()
        return self.logme

    def configure_backups(self, p_bkup_db_path: str):
        """Set location of backup and archive databases. Initialize them.

        Args:
            p_bkup_db_path (string) path to parent dir of db backup files
        """
        cfd, cfa = self.get_config_data()
        bkup_db_path, bkup_db = DB.config_bkup_db(p_bkup_db_path)
        data_rec = UT.make_dict(ST.ConfigFields.keys(), cfd)
        data_rec["bkup_db_path"] = bkup_db_path
        data_rec["bkup_db"] = bkup_db
        data_rec["arcv_db_path"] = bkup_db_path
        data_rec["arcv_db"] = bkup_db
        DB.write_db('upd', 'config', data_rec, cfa.pid)
        DB.backup_db()

    def logout_erep(self,
                    p_cfd: namedtuple):
        """Logout from eRepublik.

        Kind of guessing here. A 302 (redirect) response seems good.
        Redirecting to splash page probably.

        Args:
            p_cfd (namedtuple): data info from configs table
        """
        if self.erep_csrf_token is not None:
            formdata = {'_token': self.erep_csrf_token,
                        "remember": '1',
                        'commit': 'Logout'}
            response = self.erep_rqst.post(p_cfd.erep_url + "/logout",
                                           data=formdata,
                                           allow_redirects=True)
            if self.logme:
                msg = "Logout status code: {}".format(response.status_code)
                self.LOG.write_log(ST.LogLevel.INFO, msg)
            if response.status_code == 302:
                self.erep_csrf_token = None
                response = self.erep_rqst.get(p_cfd.erep_url)
                if self.logme:
                    msg = "Logout response/redirect text saved to log dir"
                    self.LOG.write_log(ST.LogLevel.INFO, msg)

    def get_token(self, response_text: str):
        """Get/save CSRF token.

        Args:
            response_text (string): full response text from eRep login GET
        """
        parse_text = response_text.split("var csrfToken = '")
        parse_text = parse_text[1].split("';")
        self.erep_csrf_token = parse_text[0]

    def parse_user_info(self,
                        response_text: str,
                        p_cfd: namedtuple) -> namedtuple:
        """Extract ID and name from response text.

        Args:
            response_text (string): full response text from eRep login GET
            p_cfd (namedtuple): data info from configs table

        Returns:
            namedtuple: (id_info: profile_id, user_name)
        """
        id_info = namedtuple("id_info", "profile_id user_name")
        # Get user profile ID.
        parse_text = response_text.split('"citizen":{"citizenId":')
        parse_text = parse_text[1].split(",")
        id_info.profile_id = parse_text[0]
        # Get user name.
        parse_text = response_text.split('"name":')
        parse_text = parse_text[1].split(",")
        id_info.user_name = parse_text[0].replace('"', '')
        if self.logme:
            msg = "Login response text saved to log dir"
            self.LOG.write_log(ST.LogLevel.INFO, msg)
        return id_info

    def get_local_login_file(self,
                             p_cfd: dict) -> str:
        """Use local copy of login response if available.

        Args:
            p_cfd (dict): data info from config table

        Returns:
            text or bool: full response.text from eRep login GET  or  False
        """
        login_file = path.abspath(path.join(p_cfd.log_path,
                                            "login_response"))
        response_text = False
        if Path(login_file).exists():
            with open(login_file) as lf:
                response_text = lf.read()
                lf.close()
        return response_text

    def verify_citizen_credentials(self,
                                   p_email: str,
                                   p_password: str,
                                   p_use_response_file: bool,
                                   p_logout: bool = True) -> str:
        """Login to eRepublik to confirm credentials and get profile ID.

        Args:
            p_email (str): User login email address
            p_password (str): User login password
            p_use_response_file (bool): If True, use response text file input
              if it exists.  Write response text if connecting to erep.
            p_logout (bool): If True, logout at end of method, else do not logout.
                             Optional. Default is True.

        Returns:
            text: full response.text from eRep login GET  or  None
        """
        cfd, _ = self.get_config_data()
        self.logout_erep(cfd)
        time.sleep(.300)

        response_text = False
        if p_use_response_file:
            response_text = self.get_local_login_file(cfd)
            if response_text:
                if self.logme:
                    msg = "Using cached login data for credentials"
                    self.LOG.write_log(ST.LogLevel.INFO, msg)
        if not response_text:
            formdata = {'citizen_email': p_email,
                        'citizen_password': p_password,
                        "remember": '1', 'commit': 'Login'}
            login_url = cfd.erep_url + "/login"
            response = self.erep_rqst.post(login_url,
                                           data=formdata,
                                           allow_redirects=False)
            if self.logme:
                msg = "Login status code: {}".format(response.status_code)
                self.LOG.write_log(ST.LogLevel.INFO, msg)
            if response.status_code == 302:
                response = self.erep_rqst.get(cfd.erep_url)
                self.get_token(response.text)
                response_text = response.text
                if p_use_response_file:
                    with open(path.abspath(path.join(cfd.log_path,
                              "login_response")), "w") as f:
                        f.write(response.text)
            else:
                msg = "Login connection failed. See response text in log." +\
                    "\n Probably a captcha. May want to wait a few hours."
                raise Exception(ConnectionError, msg)
        id_info = self.parse_user_info(response_text, cfd)
        self.logout_erep(cfd)
        return id_info

    def verify_api_key(self,
                       p_profile_id: str,
                       p_api_key: str) -> bool:
        """Verify that erepublik tools API key functions.

        It should return a JSON package when used with a valid profile ID.

        Args:
            p_profile_id (str): User's eRepublik Profile ID
            p_api_key (str): User's eRepublik Tools API Key

        Returns:
            bool: True if apikey works, else False
        """
        url = "https://api.erepublik.tools/v0/citizen/"
        url += str(p_profile_id)
        url += "?key={}".format(str(p_api_key))
        response = requests.get(url)
        response_text = json.loads(response.text)
        if response.status_code in (400, 404):
            msg = "Verification of eRep Tools API key failed. "
            msg += response_text["message"]
            if self.logme:
                self.LOG.write_log(ST.LogLevel.ERROR, msg)
            else:
                print(msg)
            return False
        else:
            return True

    def close_controls(self):
        """Close connections. Close the log."""
        if self.erep_csrf_token is not None:
            cfd, _ = self.get_config_data()
            self.logout_erep(cfd)
        try:
            self.LOG.close_logs()
        except Exception:
            pass

    def convert_val(self, p_erep_value) -> str:
        """Convert eRep/JSON values to Python & SQL-friendly strings.

        Args:
            p_erep_value (any): true, false, "", [], numbers
        """
        val = p_erep_value
        if p_erep_value == "true":
            val = "True"
        elif p_erep_value == "false":
            val = "False"
        elif isinstance(p_erep_value, int) or isinstance(p_erep_value, float):
            val = str(p_erep_value)
        elif p_erep_value in ("", [], {}, "[]", "{}"):
            val = "None"
        val = val.replace("'", "_")
        return val

    def get_basic_citizen_profile(self,
                                  profile_data: dict,
                                  p_citrec: dict) -> dict:
        """Extract basic citizen data from profile response.

        Args:
            profile_data (dict): returned from eRep
            p_citrec (dict): mirrors ST.CitizenFields

        Returns:
            dict: updated p_citrec
        """
        citrec = p_citrec
        citrec["name"] = profile_data["citizen"]["name"]
        citrec["is_alive"] =\
            self.convert_val(profile_data["citizen"]["is_alive"])
        citrec["is_adult"] = self.convert_val(profile_data["isAdult"])
        citrec["avatar_link"] =\
            self.convert_val(profile_data["citizen"]["avatar"])
        citrec["level"] =\
            self.convert_val(profile_data["citizen"]["level"])
        citrec["xp"] =\
            self.convert_val(
                profile_data["citizenAttributes"]["experience_points"])
        citrec["friends_count"] =\
            self.convert_val(profile_data["friends"]["number"])
        citrec["achievements_count"] =\
            self.convert_val(len(profile_data["achievements"]))
        citrec["is_in_congress"] =\
            self.convert_val(profile_data['isCongressman'])
        citrec["is_ambassador"] =\
            self.convert_val(profile_data['isAmbassador'])
        citrec["is_dictator"] =\
            self.convert_val(profile_data['isDictator'])
        citrec["is_country_president"] =\
            self.convert_val(profile_data['isPresident'])
        citrec["is_top_player"] =\
            self.convert_val(profile_data['isTopPlayer'])
        citrec["is_party_member"] =\
            self.convert_val(profile_data["isPartyMember"])
        citrec["is_party_president"] =\
            self.convert_val(profile_data["isPartyPresident"])
        return citrec

    def get_citizen_location_data(self,
                                  profile_data: dict,
                                  p_citrec: dict) -> dict:
        """Extract citizen location data from profile response.

        Args:
            profile_data (dict): returned from eRep
            p_citrec (dict): mirrors ST.CitizenFields

        Returns:
            dict: updated p_citrec
        """
        citrec = p_citrec
        citrec["citizenship_country"] =\
            self.convert_val(
                profile_data["location"]["citizenshipCountry"]["name"])
        if "city" in profile_data.keys():
            # Can also check for residenceCityId == null
            if "residenceCity" in profile_data["city"].keys():
                # May want to add city-level avatar...
                citrec["residence_city"] = self.convert_val(
                    profile_data["city"]["residenceCity"]["name"])
                citrec["residence_region"] = self.convert_val(
                    profile_data["city"]["residenceCity"]["region_name"])
                citrec["residence_country"] = self.convert_val(
                    profile_data["city"]["residenceCity"]["country_name"])
        return citrec

    def get_citizen_party_data(self,
                               profile_data: dict,
                               p_citrec: dict,
                               p_cfd: namedtuple) -> dict:
        """Extract citizen party data from profile response.

        Args:
            profile_data (dict): returned from eRep
            p_citrec (dict): mirrors ST.CitizenFields
            p_cfd (namedtuple): data from configs table

        Returns:
            dict: updated p_citrec
        """
        citrec = copy(p_citrec)
        if ("partyData" in profile_data.keys()
                and profile_data["partyData"] != []
                and not isinstance(profile_data["partyData"], bool)
                and not isinstance(profile_data["partyData"], str)):
            citrec["party_name"] =\
                self.convert_val(profile_data["partyData"]["name"])
            citrec["party_avatar_link"] = self.convert_val(
                "https:" + profile_data["partyData"]["avatar"])
            citrec["party_orientation"] = self.convert_val(
                profile_data["partyData"]["economical_orientation"])
            citrec["party_url"] = self.convert_val(
                p_cfd.erep_url + "/party/" +
                str(profile_data["partyData"]["stripped_title"]) + "-" +
                str(profile_data["partyData"]["id"]) + "/1")
        return citrec

    def get_citizen_military_data(self,
                                  profile_data: dict,
                                  p_citrec: dict,
                                  p_cfd: namedtuple) -> dict:
        """Extract citizen military data from profile response.

        Args:
            profile_data (dict): returned from eRep
            p_citrec (dict): mirrors ST.CitizenFields
            p_cfd (namedtuple): data from configs table

        Returns:
            dict: updated p_citrec
        """
        citrec = copy(p_citrec)
        if (not isinstance(profile_data["military"], bool)
                and not
                isinstance(profile_data["military"]["militaryData"], bool)):
            citrec["aircraft_rank"] = self.convert_val(
                profile_data['military']['militaryData']["aircraft"]["name"])
            citrec["ground_rank"] = self.convert_val(
                profile_data['military']['militaryData']["ground"]["name"])
        if ("militaryUnit" in profile_data["military"].keys()
                and not isinstance(profile_data["military"], bool)
                and not
                isinstance(profile_data["military"]["militaryUnit"], bool)):
            citrec["militia_name"] = self.convert_val(
                profile_data['military']['militaryUnit']['name'])
            citrec["military_rank"] = self.convert_val(
                profile_data['military']['militaryUnit']["militaryRank"])
            citrec["militia_url"] = self.convert_val(
                p_cfd.erep_url + "/military/military-unit/" +
                str(profile_data['military']['militaryUnit']['id']) +
                "/overview")
            citrec["militia_size"] = self.convert_val(
                profile_data['military']['militaryUnit']['member_count'])
            citrec["militia_avatar_link"] = self.convert_val(
                "https:" + profile_data['military']['militaryUnit']["avatar"])
        return citrec

    def get_citizen_press_data(self,
                               profile_data: dict,
                               p_citrec: dict,
                               p_cfd: namedtuple) -> dict:
        """Extract citizen presss data from profile response.

        Args:
            profile_data (dict): returned from eRep
            p_citrec (dict): mirrors ST.CitizenFields
            p_cfd (namedtuple): data and audit from configs table

        Returns:
            dict: updated p_citrec
        """
        citrec = p_citrec
        if ("newspaper" in profile_data.keys()
                and not isinstance(profile_data['newspaper'], bool)):
            citrec["newspaper_name"] = self.convert_val(
                profile_data['newspaper']['name'])
            citrec["newspaper_avatar_link"] = self.convert_val(
                "https:" + profile_data['newspaper']["avatar"])
            citrec["newspaper_url"] = self.convert_val(
                p_cfd.erep_url + "/main/newspaper/" +
                str(profile_data['newspaper']["stripped_title"]) + "-" +
                str(profile_data['newspaper']["id"]) + "/1")
        return citrec

    def get_citizen_profile(self,
                            p_profile_id: str,
                            p_use_file: bool) -> dict:
        """Retrieve profile for a citizen from eRepublik.

        Save profile data to a file and return selected values as a dict.

        Args:
            p_profile_id (str): citizen ID
            p_use_file (bool): if True and a file already exists, read it
                instead of connecting to eRep. Whether True or False, if
                connecting to eRep, save a file.

        Raises:
            ValueError if profile ID returns 404 from eRepublik

        Returns:
            dict: modeled on ST.CitizenFields dataclass
        """
        cfd, _ = self.get_config_data()
        citrec = dict()
        for cnm in ST.CitizenFields.keys():
            citrec[cnm] = copy(getattr(ST.CitizenFields, cnm))
        file_nm = "profile_response_{}".format(p_profile_id)
        profile_file = path.abspath(path.join(cfd.log_path, file_nm))
        if Path(profile_file).exists() and p_use_file:
            with open(profile_file) as pf:
                profile_data = json.loads(pf.read())
            if self.logme:
                msg = "User {} ".format(str(p_profile_id))
                msg += "profile data read from file"
                self.LOG.write_log(ST.LogLevel.DEBUG, msg)
        else:
            profile_url = cfd.erep_url +\
                "/main/citizen-profile-json/" + p_profile_id
            response = requests.get(profile_url)
            if response.status_code == 404:
                msg = "Invalid eRepublik Profile ID: {}".format(p_profile_id)
                raise Exception(ValueError, msg)
            profile_data = json.loads(response.text)
            with open(profile_file, "w") as f:
                f.write(str(response.text))
            if self.logme:
                msg = "User {} ".format(str(p_profile_id))
                msg += "profile data saved to file"
                self.LOG.write_log(ST.LogLevel.DEBUG, msg)

        citrec["profile_id"] = p_profile_id
        citrec = self.get_basic_citizen_profile(profile_data, citrec)
        citrec = self.get_citizen_location_data(profile_data, citrec)
        citrec = self.get_citizen_party_data(profile_data, citrec, cfd)
        citrec = self.get_citizen_military_data(profile_data, citrec, cfd)
        citrec = self.get_citizen_press_data(profile_data, citrec, cfd)
        return citrec

    def write_user_rec(self,
                       p_profile_id: str,
                       p_erep_email: str,
                       p_erep_passw: str,
                       p_erep_apikey: str):
        """Add or updated user record on database.

        Args:
            p_profile_id (str): verified eRep citizen profile ID
            p_erep_email (str): verified eRep login email address
            p_erep_passw (str): verified eRep login password
            p_erep_apikey (str): eRep Tools API key
        """
        urec = dict()
        for cnm in ST.UserFields.keys():
            urec[cnm] = copy(getattr(ST.UserFields, cnm))
        urec["user_erep_profile_id"] = p_profile_id
        urec["user_erep_email"] = p_erep_email
        urec["user_erep_password"] = p_erep_passw
        urec["user_tools_api_key"] = p_erep_apikey
        _, usra = self.get_database_user_data()
        if usra is None:
            DB.write_db("add", "user", urec, p_pid=None)
        else:
            DB.write_db("upd", "user", urec, p_pid=usra.pid)

    def write_citizen_rec(self, p_citrec: dict):
        """Add or modify citizen record to database.

        Args:
            p_citrec (dict): mirrors ST.CitizenFields
        """
        _, ctza = self.get_citizen_data_by_id(p_citrec["profile_id"])
        if ctza is None:
            DB.write_db("add", "citizen", p_citrec, p_pid=None)
        else:
            DB.write_db("upd", "citizen", p_citrec, p_pid=ctza.pid)

    def request_friends_list(self, profile_id: str) -> str:
        """Send PM-posting request to eRepublik.

        The PM Posting request will fail due to captcha's.
        But that's OK. We are really doing this in order to
        pull in the full friends list, which shows up in the
        response. A regular profile request only returns the
        first 20 friends.

        Always do a real login (not using file) prior to
        running this method because CSRF token must be accurate.

        Args:
            profile_id (str): citizen ID
        Returns:
            response text
        """
        cfd, _ = self.get_config_data()
        usrd, _ = self.get_database_user_data()
        self.verify_citizen_credentials(usrd.user_erep_email,
                                        usrd.user_erep_password,
                                        p_use_response_file=False,
                                        p_logout=False)
        msg_url =\
            "{}/main/messages-compose/{}".format(cfd.erep_url, profile_id)
        msg_headers = {
            "Referer": msg_url,
            "X-Requested-With": "XMLHttpRequest"}
        send_message = {
            "_token": self.erep_csrf_token,
            "citizen_name": profile_id,
            "citizen_subject": "This is a test",
            "citizen_message": "This is a test"}
        msg_response = self.erep_rqst.post(msg_url, data=send_message,
                                           headers=msg_headers,
                                           allow_redirects=False)
        if self.logme:
            msg = "Get friends list request response code: "
            msg += str(msg_response.status_code)
            self.LOG.write_log(ST.LogLevel.INFO, msg)
        with open(path.abspath(path.join(cfd.log_path,
                                         "friends_response")), "w") as f:
            f.write(msg_response.text)
        self.logout_erep(cfd)
        return msg_response.text

    def get_friends_data(self, profile_id: str):
        """Get friends list.

        Read local cached copy of previous response if it exists.

        @DEV -- add option to refresh from erep / don't use file

        Args:
            profile_id (str): citizen ID, etc.
        """
        cfd, _ = self.get_config_data()
        friends_file = path.abspath(path.join(cfd.log_path,
                                              "friends_response"))
        if Path(friends_file).exists():
            with open(friends_file) as ff:
                friends_data = ff.read()
            if self.logme:
                msg = "Using cached friends_response"
                self.LOG.write_log(ST.LogLevel.INFO, msg)
        else:
            friends_data = self.request_friends_list(profile_id)
        friends_data = friends_data.replace("\t", "").replace("\n", "")
        friends_data = friends_data.split('$j("#citizen_name").tokenInput(')
        friends_data = friends_data[1].split(', {prePopulate:')
        friends_data = json.loads(friends_data[0])
        for friend in friends_data:
            print("Getting profile for {} ... ".format(friend["name"]))
            citizen_rec = self.get_citizen_profile(friend["id"],
                                                   p_use_file=False)
            DB.write_db("add", "citizen", citizen_rec, None)
            time.sleep(.300)
        print("*** Done ***")
