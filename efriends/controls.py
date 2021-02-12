# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Manage efriends app business rules.

Module:    controls.py
Class:     Controls/0  inherits object
Author:    PQ <pq_rfw @ pm.me>
"""
import csv
import json
import sys
import time
from collections import namedtuple
from copy import copy
from os import path
from pathlib import Path
from pprint import pprint as pp  # noqa: F401

import pandas as pd
import requests

from dbase import Dbase
from logger import Logger
from structs import Structs
from texts import Texts
from utils import Utils

UT = Utils()
TX = Texts()
ST = Structs()
DB = Dbase(ST)
UT = Utils()


class Controls(object):
    """Rules engine for efriends."""

    def __init__(self):
        """Initialize Controls object."""
        self.logme = False

    def check_python_version(self):
        """Validate Python version."""
        if sys.version_info[:2] < (3, 6):
            msg = TX.shit.f_py3_req
            msg += "\n{}".format(TX.shit.f_user_ver)
            version = "{}.{}.{}".format(*sys.version_info)
            msg.replace("~VERSION~", version)
            raise Exception(EnvironmentError, msg)

    def set_erep_headers(self):
        """Set request headers for eRepublik calls."""
        self.erep_csrf_token = None
        self.erep_rqst = requests.Session()
        self.erep_rqst.headers = None
        self.erep_rqst.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;' +
                      'q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) ' +
                          'AppleWebKit/537.36 (KHTML, like Gecko) ' +
                          'Ubuntu Chromium/31.0.1650.63 ' +
                          'Chrome/31.0.1650.63 Safari/537.36'}
        self.etools_rqst = requests.Session()
        self.etools_ctzn_bynm_url =\
            "https://api.erepublik.tools/v0/citizen?" +\
            "name=~NAME~&page=1&key=~KEY~"

    def configure_database(self):
        """Instantiate Dbase object.

        Create local app file, db directories if needed.
        Create main DB file and tables if needed.
        """
        HOME = UT.get_home()
        app_path = path.join(HOME, TX.dbs.lcl_path)
        if not Path(app_path).exists():
            UT.exec_bash(["mkdir {}".format(app_path)])
            for f_path in (TX.dbs.db_path, TX.dbs.cache_path, TX.dbs.log_path,
                           TX.dbs.bkup_path, TX.dbs.arcv_path):
                mk_path = path.join(HOME, f_path)
                UT.exec_bash(["mkdir {}".format(mk_path)])
        DB.create_main_db()
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

    def get_user_db_record(self) -> tuple:
        """Query data base for most current user record, decrypted."""
        return self.convert_data_record(
            DB.query_user())

    def get_ctzn_db_rec_by_id(self, p_profile_id: str) -> tuple:
        """Query data base for most current citizen record.

        Args:
            p_profile_id (str) a valid citizen ID
        """
        return self.convert_data_record(
            DB.query_citizen_by_profile_id(p_profile_id))

    def get_citizen_db_rec_by_nm(self, p_citzn_nm: str) -> tuple:
        """Query data base for most current citizen record.

        Args:
            p_citzn_nm (str) a valid citizen name
        """
        return self.convert_data_record(
            DB.query_citizen_by_name(p_citzn_nm))

    def enable_logging(self,
                       p_log_level: str = 'INFO'):
        """Assign log file location. Instantiate Logger object.

        Args:
            p_log_level (str): valid logging level key. Default=INFO.
        """
        if not self.logme:
            if p_log_level is None or p_log_level not in ST.LogLevel.keys():
                p_log_level = 'INFO'
            log_level = getattr(ST.LogLevel, p_log_level)
            if (log_level != ST.LogLevel.NOTSET):
                log_path = path.join(UT.get_home(), TX.dbs.log_path)
                if not Path(log_path).exists():
                    msg = "{}{}".format(TX.shit.f_bad_log_path, log_path)
                    raise Exception(IOError, msg)
                log_full_path = path.join(log_path, TX.dbs.log_name)
                self.logme = True
                self.LOG = Logger(log_full_path, log_level)
                self.LOG.set_log()
                msg = TX.logm.ll_log_loc + log_full_path
                self.LOG.write_log(ST.LogLevel.INFO, msg)
                msg = TX.logm.ll_log_lvl + p_log_level
                self.LOG.write_log(ST.LogLevel.INFO, msg)

    def create_log(self,
                   p_log_level: str = 'INFO') -> bool:
        """Update config data with path to log file and log level.

        Args:
            p_log_level (string) valid key to ST.LogLevel. Default = 'INFO'.

        Returns:
            bool: True if logging successfully turned on, else False
        """
        self.logme = False
        if p_log_level not in ST.LogLevel.keys():
            msg = TX.shit.f_log_lvl_req + str(ST.LogLevel.keys)
            raise Exception(ValueError, msg)

        self.enable_logging(p_log_level)
        return self.logme

    def create_bkupdb(self):
        """Create backup database."""
        bkup_path = path.join(UT.get_home(), TX.dbs.bkup_path)
        if not Path(bkup_path).exists():
            msg = "{}{}".format(TX.shit.f_bad_log_path, bkup_path)
            raise Exception(IOError, msg)
        arcv_path = path.join(UT.get_home(), TX.dbs.arcv_path)
        if not Path(arcv_path).exists():
            msg = "{}{}".format(TX.shit.f_bad_log_path, arcv_path)
            raise Exception(IOError, msg)
        DB.backup_db()

    def logout_erep(self):
        """Logout from eRepublik. Assume 302 (redirect) is good response."""
        if self.erep_csrf_token is not None:
            formdata = {'_token': self.erep_csrf_token,
                        "remember": '1',
                        'commit': 'Logout'}
            response = self.erep_rqst.post(TX.urls.u_erep + "/logout",
                                           data=formdata,
                                           allow_redirects=True)
            if self.logme:
                msg = TX.logm.ll_logout_cd + str(response.status_code)
                self.LOG.write_log(ST.LogLevel.INFO, msg)
            if response.status_code == 302:
                self.erep_csrf_token = None
                response = self.erep_rqst.get(TX.urls.u_erep)
                if self.logme:
                    msg = TX.logm.ll_save_logout_resp
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
                        response_text: str) -> namedtuple:
        """Extract ID and name from response text.

        Args:
            response_text (string): full response text from eRep login GET

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
            msg = TX.logm.ll_save_login_resp
            self.LOG.write_log(ST.LogLevel.INFO, msg)
        return id_info

    def get_cached_login_file(self) -> str:
        """Use local copy of login response if available.

        Returns:
            text or bool: full response.text from eRep login GET  or  False
        """
        cache_file = path.join(UT.get_home(), TX.dbs.cache_path,
                               "login_response")
        response_text = False
        if Path(cache_file).exists():
            with open(cache_file) as lf:
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
            p_logout (bool): If True, logout at end of method,
                             else do not logout. Optional. Default is True.

        Returns:
            text: full response.text from eRep login GET  or  None
        """
        self.logout_erep()
        time.sleep(.300)
        response_text = False
        if p_use_response_file:
            response_text = self.get_cached_login_file()
            if response_text:
                if self.logme:
                    msg = TX.logm.ll_cached_login
                    self.LOG.write_log(ST.LogLevel.INFO, msg)
        if not response_text:
            formdata = {'citizen_email': p_email,
                        'citizen_password': p_password,
                        "remember": '1', 'commit': 'Login'}
            login_url = TX.urls.u_erep + "/login"
            response = self.erep_rqst.post(login_url,
                                           data=formdata,
                                           allow_redirects=False)
            if self.logme:
                msg = TX.logm.ll_login_cd + str(response.status_code)
                self.LOG.write_log(ST.LogLevel.INFO, msg)
            if response.status_code == 302:
                response = self.erep_rqst.get(TX.urls.u_erep)
                self.get_token(response.text)
                response_text = response.text
                if p_use_response_file:
                    cache_file = path.join(UT.get_home(), TX.dbs.cache_path,
                                           "login_response")
                    with open(cache_file, "w") as f:
                        f.write(response.text)
            else:
                msg = TX.shit.f_login_failed
                raise Exception(ConnectionError, msg)
        id_info = self.parse_user_info(response_text)
        self.logout_erep()
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
            msg = TX.shit.f_apikey_failed + response_text["message"]
            if self.logme:
                self.LOG.write_log(ST.LogLevel.ERROR, msg)
            else:
                print(msg)
            return False
        else:
            return True

    def close_controls(self):
        """Close connections. Close the log."""
        # This is causing a connection problem for some reason...
        # if self.erep_csrf_token is not None:
        #     self.logout_erep()
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
                               p_citrec: dict) -> dict:
        """Extract citizen party data from profile response.

        Args:
            profile_data (dict): returned from eRep
            p_citrec (dict): mirrors ST.CitizenFields

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
                TX.urls.u_erep + "/party/" +
                str(profile_data["partyData"]["stripped_title"]) + "-" +
                str(profile_data["partyData"]["id"]) + "/1")
        return citrec

    def get_citizen_military_data(self,
                                  profile_data: dict,
                                  p_citrec: dict) -> dict:
        """Extract citizen military data from profile response.

        Args:
            profile_data (dict): returned from eRep
            p_citrec (dict): mirrors ST.CitizenFields

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
                TX.urls.u_erep + "/military/military-unit/" +
                str(profile_data['military']['militaryUnit']['id']) +
                "/overview")
            citrec["militia_size"] = self.convert_val(
                profile_data['military']['militaryUnit']['member_count'])
            citrec["militia_avatar_link"] = self.convert_val(
                "https:" + profile_data['military']['militaryUnit']["avatar"])
        return citrec

    def get_citizen_press_data(self,
                               profile_data: dict,
                               p_citrec: dict) -> dict:
        """Extract citizen presss data from profile response.

        Args:
            profile_data (dict): returned from eRep
            p_citrec (dict): mirrors ST.CitizenFields

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
                TX.urls.u_erep + "/main/newspaper/" +
                str(profile_data['newspaper']["stripped_title"]) + "-" +
                str(profile_data['newspaper']["id"]) + "/1")
        return citrec

    def get_ctzn_profile_from_erep(self,
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
        citrec = dict()
        for cnm in ST.CitizenFields.keys():
            citrec[cnm] = copy(getattr(ST.CitizenFields, cnm))
        cache_file = path.join(UT.get_home(), TX.dbs.cache_path,
                               "profile_response_{}".format(p_profile_id))
        if Path(cache_file).exists() and p_use_file:
            with open(cache_file) as pf:
                profile_data = json.loads(pf.read())
            if self.logme:
                msg = TX.logm.ll_cached_profile + str(p_profile_id)
                self.LOG.write_log(ST.LogLevel.DEBUG, msg)
        else:
            profile_url = TX.urls.u_erep +\
                "/main/citizen-profile-json/" + p_profile_id
            response = requests.get(profile_url)
            if response.status_code == 404:
                msg = TX.shit.f_profile_id_failed + p_profile_id
                raise Exception(ValueError, msg)
            profile_data = json.loads(response.text)
            with open(cache_file, "w") as f:
                f.write(str(response.text))
            if self.logme:
                msg = TX.logm.ll_profile_file_cached + p_profile_id
                self.LOG.write_log(ST.LogLevel.DEBUG, msg)

        citrec["profile_id"] = p_profile_id
        citrec = self.get_basic_citizen_profile(profile_data, citrec)
        citrec = self.get_citizen_location_data(profile_data, citrec)
        citrec = self.get_citizen_party_data(profile_data, citrec)
        citrec = self.get_citizen_military_data(profile_data, citrec)
        citrec = self.get_citizen_press_data(profile_data, citrec)
        return citrec

    def write_user_rec(self,
                       p_profile_id: str,
                       p_erep_email: str,
                       p_erep_passw: str,
                       p_erep_apikey: str = None):
        """Add or update user record on database.

        Args:
            p_profile_id (str): verified eRep citizen profile ID.
            p_erep_email (str): verified eRep login email address.
            p_erep_passw (str): verified eRep login password.
            p_erep_apikey (str): eRep Tools API key. Optional.
        """
        urec = dict()
        for cnm in ST.UserFields.keys():
            urec[cnm] = copy(getattr(ST.UserFields, cnm))
        urec["user_erep_profile_id"] = p_profile_id
        urec["user_erep_email"] = p_erep_email
        urec["user_erep_password"] = p_erep_passw
        if p_erep_apikey is not None:
            urec["user_tools_api_key"] = p_erep_apikey
        _, usra = self.get_user_db_record()
        if usra is None:
            DB.write_db("add", "user", urec, p_oid=None)
        else:
            DB.write_db("upd", "user", urec, p_oid=usra.oid)

    def write_ctzn_rec(self, p_citrec: dict):
        """Add or modify citizen record to database.

        Args:
            p_citrec (dict): mirrors ST.CitizenFields
        """
        _, ctza = self.get_ctzn_db_rec_by_id(p_citrec["profile_id"])
        if ctza is None:
            DB.write_db("add", "citizen", p_citrec, p_oid=None)
        else:
            DB.write_db("upd", "citizen", p_citrec, p_oid=ctza.oid)

    def request_friends_list(self, p_profile_id: str) -> str:
        """Send PM-posting request to eRepublik.

        The PM Posting request will fail due to captcha's.
        But that's OK. We are really doing this in order to
        pull in the full friends list, which shows up in the
        response. A regular profile request only returns the
        first 20 friends.

        Do interactive login, not using cached response,
        because CSRF token must be fresh.

        Args:
            p_profile_id (str): citizen ID
        Returns:
            response text
        """
        usrd, _ = self.get_user_db_record()
        self.verify_citizen_credentials(usrd.user_erep_email,
                                        usrd.user_erep_password,
                                        p_use_response_file=False,
                                        p_logout=False)
        msg_url =\
            "{}/main/messages-compose/{}".format(TX.urls.u_erep, p_profile_id)
        msg_headers = {
            "Referer": msg_url,
            "X-Requested-With": "XMLHttpRequest"}
        send_message = {
            "_token": self.erep_csrf_token,
            "citizen_name": p_profile_id,
            "citizen_subject": "This is a test",
            "citizen_message": "This is a test"}
        msg_response = self.erep_rqst.post(msg_url, data=send_message,
                                           headers=msg_headers,
                                           allow_redirects=False)
        if self.logme:
            msg = TX.logm.ll_friends_cd + str(msg_response.status_code)
            self.LOG.write_log(ST.LogLevel.INFO, msg)
        cache_file = path.join(UT.get_home(), TX.dbs.cache_path,
                               "friends_response")
        with open(cache_file, "w") as f:
            f.write(msg_response.text)
        self.logout_erep()
        return msg_response.text

    def get_erep_citizen_by_id(self,
                               p_profile_id: str,
                               p_use_file: bool = False,
                               p_is_friend: bool = False) -> bool:
        """Get citizen data from eRepublik and store in database.

        Args:
            p_profile_id (string): eRepublik citizen profile ID
            p_use_file (bool, optional): Defaults to False. If True
                and a cached file exists, use that instead of
                calling eRepublik API.
            p_is_friend (bool, optional): Defaults to False. If True
                then set "is_user_friend" value to "True" on DB

        Returns:
            bool: True if citizen data retrieved and stored, else False
        """
        ctzn_rec = self.get_ctzn_profile_from_erep(p_profile_id,
                                                   p_use_file=False)
        if ctzn_rec:
            ctzn_rec["is_user_friend"] = "True" if p_is_friend else "False"
            ctzd, ctza = self.get_ctzn_db_rec_by_id(ctzn_rec["profile_id"])
            if ctza in (None, "None", ""):
                DB.write_db("add", "citizen", ctzn_rec, None)
            else:
                ctzn_rec["is_user_friend"] = ctzd.is_user_friend
                DB.write_db("upd", "citizen", ctzn_rec, p_oid=ctza.oid)
            time.sleep(.300)
            return True
        else:
            return False

    def get_erep_citizen_by_nm(self,
                               p_api_key: str,
                               p_citizen_nm: str,
                               p_use_file: bool = False,
                               p_is_friend: bool = False) -> bool:
        """Get citizen ID by looking up name in erepublik.tools API.

        Then get citizen data from eRepublik and store in database.

        Args:
            p_api_key (string): user's erepublik.tools API key
            p_profile_nm (string): eRepublik citizen name
            p_use_file (bool, optional): Defaults to False. If True
                and a cached file exists, use that instead of
                calling eRepublik API.
            p_is_friend (bool, optional): Defaults to False. If True
                then set "is_user_friend" value to "True" on DB

        Returns:
            bool: True if citizen data retrieved and stored, else False
        """
        etools_url = self.etools_ctzn_bynm_url.replace("~NAME~", p_citizen_nm)
        etools_url = etools_url.replace("~KEY~", p_api_key)
        response = self.etools_rqst.get(etools_url)
        response_json = json.loads(response.text)
        profile_id = str(response_json["citizen"][0]["id"]).strip()
        return self.get_erep_citizen_by_id(profile_id, False, p_is_friend)

    def get_erep_ctzn_by_id_list(self,
                                 p_id_list: list) -> bool:
        """Pull citizen data from eRep based on list of IDs.

        Args:
            p_id_list (list): list of valid citizen profile IDs

        Returns:
            tuple: (bool: True if file processed OK, else False,
                    str: detail-level message)
        """
        count_hits = 0
        err = None
        for profile_id in p_id_list:
            print(TX.msg.n_lookup_id + profile_id)
            ok = self.get_erep_citizen_by_id(profile_id)
            if ok:
                count_hits += 1
            else:
                err = TX.shit.f_profile_id_failed + profile_id
        msg = TX.msg.n_profiles_done + str(count_hits)
        if err is not None:
            msg += "\n{}".format(err)
            return (False, msg)
        else:
            return (True, msg)

    def refresh_ctzn_data_from_db(self) -> tuple:
        """Query data base for list of all active profile IDs.

        Returns:
            tuple: (bool: True if file processed OK, else False,
                    str: detail-level message)
        """
        id_list = DB.query_for_profile_id_list()
        msg = TX.msg.n_profiles_pulled + str(len(id_list))
        status, msg_2 = self.get_erep_ctzn_by_id_list(id_list)
        msg += "\n{}".format(msg_2)
        return(status, msg)

    def refresh_citizen_data_from_file(self,
                                       p_id_list_path: str) -> tuple:
        """Read list of IDs from file and pull citizen data from eRep.

        Args:
            p_id_list_path (str): full path to file of profile IDs

        Returns:
            tuple: (bool: True if file processed OK, else False,
                    str: detail-level message)
        """
        if not Path(p_id_list_path).exists():
            return (False, "File could not be found")
        with open(p_id_list_path) as idf:
            id_list = idf.read()
            idf.close()
        id_list = id_list.replace('"', "")
        id_list = id_list.replace("'", "")
        id_list = id_list.replace(",", "\n")
        id_list = id_list.replace(";", "\n")
        id_list = id_list.replace(":", "\n")
        id_list = id_list.replace("\t", "\n")
        id_list = id_list.replace("~", "\n")
        id_list = id_list.strip()
        id_list = id_list.split("\n")
        id_list = [i for i in id_list if i not in (" ", "")]
        return self.get_erep_ctzn_by_id_list(id_list)

    def get_erep_friends_data(self,
                              p_profile_id: str,
                              p_use_file: bool = False):
        """Get user's friends list. Gather citizen profile data for friends.

        DO a read-only, non-login GET to pull in citizen profile data.
        This could be replaced with a call to the erepublik.tools API, but
        then data might be slightly less fresh than calling eRep directly.

        Wait 300 milliseconds between calls. Avoid looking like DDOS attack.
        This is about 3 citizens per second. Pulling data takes about one
        minute for every 180 citizens.

        Args:
            p_profile_id (str): citizen ID of user
            p_use_file (bool): If True use cached Friends List if it exists,
                            else Post to eRep to refresh user's friends list
        Returns:
            str: detail-level message about successful calls
        """
        cache_file = path.join(UT.get_home(), TX.dbs.cache_path,
                               "friends_response")
        if p_use_file and Path(cache_file).exists():
            with open(cache_file) as ff:
                friends_data = ff.read()
                ff.close()
            if self.logme:
                msg = TX.logm.ll_cached_friends
                self.LOG.write_log(ST.LogLevel.INFO, msg)
        else:
            friends_data = self.request_friends_list(p_profile_id)
        friends_data = friends_data.replace("\t", "").replace("\n", "")
        friends_data = friends_data.split('$j("#citizen_name").tokenInput(')
        friends_data = friends_data[1].split(', {prePopulate:')
        friends_data = json.loads(friends_data[0])
        count_hits = 0
        msg = None
        for friend in friends_data:
            print(TX.msg.n_lookup_nm + friend["name"])
            self.get_erep_citizen_by_id(friend["id"],
                                        p_use_file=False,
                                        p_is_friend=True)
            count_hits += 1
        print(TX.msg.n_finito)
        msg = TX.msg.n_friends_pulled + str(count_hits)
        return msg

    def run_citizen_viz(self,
                        p_qry_nm: str,
                        p_file_types: list):
        """Execute database query, format and deliver results

        Will want another class for to do publish/formatting stuff.

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

        Args:
            p_qry_nm (str): ID of SQL query, like "q0100"
            p_file_types (list): one or more output file formats

        For creating PDFs, see:
        - https://realpython.com/creating-modifying-pdf/#creating-a-pdf-file-from-scratch
        - https://www.reportlab.com/software/opensource/rl-toolkit/
        - https://pypi.org/project/pdfrw/#writing-pdfs
        - https://www.adobe.com/content/dam/acom/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf

        """
        # Can probably make this a bit more dynamic, but
        # want to be careful to avoid SQL injection attack vectors.
        # Not a huge concern, but still... Maybe scan for DELETE,
        # UPDATE, INSERT, DROP... or verify that there is a
        # comment which has some kind of token?
        sql_files = {
            "q0100": "q0100_country_party_count.sql"
        }
        if p_qry_nm not in sql_files.keys():
            return False
        result = DB.query_citizen_sql(sql_files[p_qry_nm])
        headers = result.pop(0)
        file_nm = sql_files[p_qry_nm].replace(".sql", "")
        file_path = path.join(UT.get_home(), TX.dbs.cache_path)
        data_l = list()
        for data_sql in result:
            data_d = dict()
            for cx, val in enumerate(list(data_sql)):
                data_d[headers[cx]] = val
            data_l.append(data_d)

        return_pkg = dict()
        if "json" in p_file_types:
            file_full_path = path.join(file_path, file_nm + ".json")
            return_pkg["json"] = file_full_path
            with open(file_full_path, 'w') as jf:
                jf.write(json.dumps(data_l))
            jf.close()
        if "csv" in p_file_types\
        or "html" in p_file_types\
        or "df" in p_file_types:
            file_full_path = path.join(file_path, file_nm + ".csv")
            if "csv" in p_file_types:
                return_pkg["csv"] = file_full_path
            with open(file_full_path, 'w') as cf:
                writer = csv.writer(cf, delimiter=",", quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
                writer.writerow(headers)
                for data in data_l:
                    data_row = list()
                    for _, val in data.items():
                        data_row.append(val)
                    writer.writerow(data_row)
            cf.close()
            if "html" in p_file_types or "df" in p_file_types:
                # This creates a dataframe:
                data = pd.read_csv(file_full_path)
                # Note that pandas can also write directly to a sqlite DB using...
                # data.to_sql('table-nm', '<db-connection>', ...)
                # See: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_sql.html#pandas.DataFrame.to_sql
                # Parquet, hdf5 and other formats also supported

                if "df" in p_file_types:
                    file_full_path = path.join(file_path, file_nm + ".pkl")
                    return_pkg["df"] = file_full_path
                    data.to_pickle(file_full_path)
                if "html" in p_file_types:
                    file_full_path = path.join(file_path, file_nm + ".html")
                    return_pkg["html"] = file_full_path
                    with open(file_full_path, 'w') as hf:
                        hf.write(data.to_html())
                    hf.close()
        return(return_pkg)

