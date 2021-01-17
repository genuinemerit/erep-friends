# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Manage eRepublik friends data and rules.

Module:    controls.py
Class:     Controls/0  inherits object
Author:    PQ <pq_rfw @ pm.me>
"""
import fnmatch
import getpass
import json
import sys
import time
import tkinter as tk
from collections import namedtuple
from copy import copy
from os import listdir, mkdir, path
from pathlib import Path
from pprint import pprint as pp  # noqa: F401
from tkinter import messagebox, ttk

import requests
from tornado.options import define, options

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
        """Initialize Controls() object.

        @DEV - Need to work on getting Logging turned on
               when log credentials have already been
               established / are not changed.
        """
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
            cfg_rec = dict()
            for cnm in ST.ConfigFields.keys():
                cfg_rec[cnm] = copy(getattr(ST.ConfigFields, cnm))
            DB.write_db('add', 'config', cfg_rec)
        return ST

    def get_config_data(self):
        """Query data base for most current config record

        Returns:
            object  or  bool: False if no result,
                              else dict of "data" and "audit" dataclasses
        """
        data_rows = DB.query_config()
        if len(data_rows) < 1:
            return False
        else:
            return data_rows

    def get_database_user_data(self):
        """Query data base for most current user record, decrypted

        Returns:
            object  or  bool: False if no result,
                              else dict of "data" and "audit" dataclasses
        """
        data_rows = DB.query_user(p_decrypt=True)
        if len(data_rows) < 1:
            return False
        else:
            return data_rows

    def enable_logging(self):
        """Assign log file location. Instantiate Logger object."""
        cfg_rec = self.get_config_data()
        self.logme = False\
            if cfg_rec["data"].log_level == ST.LogLevel.NOTSET\
            else True
        log_file = path.join(cfg_rec["data"].log_path,
                             cfg_rec["data"].log_name)
        self.LOG = Logger(log_file, cfg_rec["data"].log_level)
        self.LOG.set_log()
        if self.logme:
            msg = "Log file location: {}".format(log_file)
            self.LOG.write_log(ST.LogLevel.INFO, msg)
            msg = "Log level: {}".format(cfg_rec["data"].log_level)
            self.LOG.write_log(ST.LogLevel.INFO, msg)

    def configure_log(self,
                      p_log_path: str,
                      p_log_level: str):
        """Update configs and options with path to log file and log level.

        Args:
            p_log_path (string) path to parent dir of log file
            p_log_level (string) valid key to ST.LogLevel

        @DEV - either add a flag or (better) identify condition that
               indicates logging has been configured and turned on or not
        """
        self.logme = False
        if p_log_path and p_log_path not in (None, "None"):
            log_path = path.abspath(path.realpath(p_log_path))
            if not Path(log_path).exists():
                msg = "Log file path does not exist." +\
                    "\nUser must create directory or pick a valid one."
                raise Exception(IOError, msg)
            log_level = p_log_level
            if log_level not in ST.LogLevel.keys():
                msg = "Log level must be one of: " + str(ST.LogLevel.keys)
                raise Exception(ValueError, msg)
            cfgr = self.get_config_data()
            if not cfgr:
                msg = "System not initialized properly. " +\
                    "Delete DB file and restart."
                raise Exception(ValueError, msg)
            mod_rec = dict()
            for cnm in ST.ConfigFields.keys():
                mod_rec[cnm] = copy(getattr(cfgr["data"], cnm))
                mod_rec["log_path"] = log_path
                mod_rec["log_level"] = log_level
            DB.write_db('upd', 'config', mod_rec, cfgr["audit"].pid)
            cfgr = self.get_config_data()
            if cfgr["data"].log_path\
            and cfgr["data"].log_path not in (None, "None"):
                self.enable_logging()

    def configure_backups(self,
                          p_bkup_db_path: str):
        """Set location of backup and archive databases. Initialize them.

        Args:
            p_bkup_db_path (string) path to parent dir of db backup files
        """
        bkup_db_path, arcv_db_path, bkup_db, arcv_db =\
            DB.config_bkup_db(p_bkup_db_path)
        cfgr = self.get_config_data()
        if not cfgr:
            msg = "System not initialized properly. " +\
                  "Delete DB file and restart."
            raise Exception(ValueError, msg)
        cfg_rec = dict()
        for cnm in ST.ConfigFields.keys():
            cfg_rec[cnm] = copy(getattr(cfgr["data"], cnm))
        cfg_rec["bkup_db_path"] = bkup_db_path
        cfg_rec["bkup_db"] = bkup_db
        cfg_rec["arcv_db_path"] = arcv_db_path
        cfg_rec["arcv_db"] = arcv_db
        DB.write_db('upd', 'config', cfg_rec, cfgr["audit"].pid)
        DB.backup_db()
        DB.archive_db()

    def logout_erep(self):
        """Logout from eRepublik.

        Kind of guessing here. A 302 (redirect) response seems good.
        Redirecting to splash page probably.
        """
        if self.erep_csrf_token is not None:
            formdata = {'_token': self.erep_csrf_token,
                        "remember": '1',
                        'commit': 'Logout'}
            response = self.erep_rqst.post(self.cfgd["data"].erep_url + "/logout",
                                           data=formdata,
                                           allow_redirects=True)
            if self.logme:
                msg = "Logout status code: {}".format(response.status_code)
                self.LOG.write_log(ST.LogLevel.INFO, msg)
            if response.status_code == 302:
                self.erep_csrf_token = None
                response = self.erep_rqst.get(self.cfgd["data"].erep_url)
                if self.logme:
                    msg = "Logout response/redirect text: " + response.text
                    self.LOG.write_log(ST.LogLevel.INFO, msg)

    def get_token(self, response_text: str):
        """Get/save CSRF token.

        Args:
            response_text (string): full response text from eRep login GET
        """
        parse_text = response_text.split("var csrfToken = '")
        parse_text = parse_text[1].split("';")
        self.erep_csrf_token = parse_text[0]

    def get_basic_user_info(self, response_text: str):
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
        if self.logme and self.cfgd["data"].log_level == 'DEBUG':
            msg = "CSRF Token:\t{}".format(self.erep_csrf_token)
            self.LOG.write_log(ST.LogLevel.INFO, msg)
            msg = "Login response:\n{}".format(response_text)
            self.LOG.write_log(ST.LogLevel.INFO, msg)
        return id_info

    def get_local_login_file(self):
        """Use local copy of login response if available.

        Returns:
            text or bool: full response.text from eRep login GET  or  False
        """
        login_file = path.abspath(path.join(self.cfgd["data"].log_path,
                                            "login_response"))
        response_text = False
        if Path(login_file).exists():
            with open(login_file) as lf:
                response_text = lf.read()
                lf.close()
        return response_text

    def login_erep(self,
                   p_email: str,
                   p_password: str,
                   p_use_response_file: bool) -> str:
        """Login to eRepublik to confirm credentials and get profile ID.

        Args:
            p_email (str): User login email address
            p_password (str): User login password
            p_use_response_file (bool): If True, use response text file input
              if it exists.  Write response text if connecting to erep.

        Returns:
            text: full response.text from eRep login GET  or  None
        """
        self.cfgd = self.get_config_data()
        self.logout_erep()
        time.sleep(.300)

        response_text = False
        if p_use_response_file:
            response_text = self.get_local_login_file()
            if response_text:
                if self.logme:
                    msg = "Using cached login data for credentials"
                    self.LOG.write_log(ST.LogLevel.INFO, msg)
        if not response_text:
            formdata = {'citizen_email': p_email,
                        'citizen_password': p_password,
                        "remember": '1', 'commit': 'Login'}
            login_url = self.cfgd["data"].erep_url + "/login"
            response = self.erep_rqst.post(login_url,
                                           data=formdata,
                                           allow_redirects=False)
            if self.logme:
                msg = "Login status code: {}".format(response.status_code)
                self.LOG.write_log(ST.LogLevel.INFO, msg)
            if response.status_code == 302:
                response = self.erep_rqst.get(self.cfgd["data"].erep_url)
                self.get_token(response.text)
                response_text = response.text
                if p_use_response_file:
                    with open(path.abspath(path.join(self.cfgd["data"].log_path,
                              "login_response")), "w") as f:
                        f.write(response.text)
            else:
                msg = "Login connection failed. See response text in log." +\
                    "\n Probably a captcha. May want to wait a few hours."
                raise Exception(ConnectionError, msg)
        id_info = self.get_basic_user_info(response_text)
        self.logout_erep()
        return id_info

    def close_controls(self):
        """Close connections. Close the log."""
        if self.erep_csrf_token is not None:
            self.logout_erep()
        try:
            self.LOG.close_logs()
        except Exception:
            pass

    def convert_val(self, p_erep_value) -> str:
        """Convert eRep/JSON values to SQL- and Python-friendlier strings."

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
                                  p_frec: dict) -> dict:
        """Extract basic citizen data from profile response.

        Args:
            profile_data (dict): returned from eRep
            p_frec (dict): mirrors ST.FriendsFields

        Returns:
            dict: updated p_frec
        """
        frec = p_frec
        frec["name"] = profile_data["citizen"]["name"]
        frec["is_alive"] =\
            self.convert_val(profile_data["citizen"]["is_alive"])
        frec["is_adult"] = self.convert_val(profile_data["isAdult"])
        frec["avatar_link"] = self.convert_val(profile_data["citizen"]["avatar"])
        frec["level"] =\
            self.convert_val(profile_data["citizen"]["level"])
        frec["xp"] =\
            self.convert_val(
                profile_data["citizenAttributes"]["experience_points"])
        frec["friends_count"] =\
            self.convert_val(profile_data["friends"]["number"])
        frec["achievements_count"] =\
            self.convert_val(len(profile_data["achievements"]))
        frec["is_in_congress"] =\
            self.convert_val(profile_data['isCongressman'])
        frec["is_ambassador"] = self.convert_val(profile_data['isAmbassador'])
        frec["is_dictator"] = self.convert_val(profile_data['isDictator'])
        frec["is_country_president"] =\
            self.convert_val(profile_data['isPresident'])
        frec["is_top_player"] = self.convert_val(profile_data['isTopPlayer'])
        frec["is_party_member"] = self.convert_val(profile_data["isPartyMember"])
        frec["is_party_president"] =\
            self.convert_val(profile_data["isPartyPresident"])
        return frec

    def get_citizen_location_data(self,
                                  profile_data: dict,
                                  p_frec: dict) -> dict:
        """Extract citizen location data from profile response.

        Args:
            profile_data (dict): returned from eRep
            p_frec (dict): mirrors ST.FriendsFields

        Returns:
            dict: updated p_frec
        """
        frec = p_frec
        frec["citizenship_country"] =\
            self.convert_val(
                profile_data["location"]["citizenshipCountry"]["name"])
        if "city" in profile_data.keys():
            frec["residence_city"] = self.convert_val(
                profile_data["city"]["residenceCity"]["name"])
            frec["residence_region"] = self.convert_val(
                profile_data["city"]["residenceCity"]["region_name"])
            frec["residence_country"] = self.convert_val(
                profile_data["city"]["residenceCity"]["country_name"])
        return frec

    def get_citizen_party_data(self,
                               profile_data: dict,
                               p_frec: dict) -> dict:
        """Extract citizen party data from profile response.

        Args:
            profile_data (dict): returned from eRep
            p_frec (dict): mirrors ST.FriendsFields

        Returns:
            dict: updated p_frec
        """
        frec = p_frec
        if "partyData" in profile_data.keys()\
          and profile_data["partyData"] != []\
          and not isinstance(profile_data["partyData"], bool)\
          and not isinstance(profile_data["partyData"], str):
            frec["party_name"] =\
                self.convert_val(profile_data["partyData"]["name"])
            frec["party_avatar_link"] = self.convert_val(
                "https:" + profile_data["partyData"]["avatar"])
            frec["party_orientation"] = self.convert_val(
                profile_data["partyData"]["economical_orientation"])
            frec["party_url"] = self.convert_val(
                self.cfgd["data"].erep_url + "/party/" +\
                str(profile_data["partyData"]["stripped_title"]) + "-" +\
                str(profile_data["partyData"]["id"]) + "/1")
        return frec

    def get_citizen_military_data(self,
                                  profile_data: dict,
                                  p_frec: dict) -> dict:
        """Extract citizen military data from profile response.

        Args:
            profile_data (dict): returned from eRep
            p_frec (dict): mirrors ST.FriendsFields

        Returns:
            dict: updated p_frec
        """
        frec = p_frec
        if not isinstance(profile_data["military"], bool)\
          and not isinstance(profile_data["military"]["militaryData"], bool):
            frec["aircraft_rank"] = self.convert_val(
                profile_data['military']['militaryData']["aircraft"]["name"])
            frec["ground_rank"] = self.convert_val(
                profile_data['military']['militaryData']["ground"]["name"])
        if "militaryUnit" in profile_data["military"].keys()\
          and not isinstance(profile_data["military"], bool)\
          and not isinstance(profile_data["military"]["militaryUnit"], bool):
            frec["militia_name"] = self.convert_val(
                profile_data['military']['militaryUnit']['name'])
            frec["military_rank"] = self.convert_val(
                profile_data['military']['militaryUnit']["militaryRank"])
            frec["militia_url"] = self.convert_val(
                self.cfgd["data"].erep_url +\
                "/military/military-unit/" +\
                str(profile_data['military']['militaryUnit']['id']) +\
                "/overview")
            frec["militia_size"] = self.convert_val(
                profile_data['military']['militaryUnit']['member_count'])
            frec["militia_avatar_link"] = self.convert_val(
                "https:" + profile_data['military']['militaryUnit']["avatar"])
        return frec

    def get_citizen_press_data(self,
                               profile_data: dict,
                               p_frec: dict) -> dict:
        """Extract citizen presss data from profile response.

        Args:
            profile_data (dict): returned from eRep
            p_frec (dict): mirrors ST.FriendsFields

        Returns:
            dict: updated p_frec
        """
        frec = p_frec
        if "newspaper" in profile_data.keys()\
          and not isinstance(profile_data['newspaper'], bool):
            frec["newspaper_name"] = self.convert_val(
                profile_data['newspaper']['name'])
            frec["newspaper_avatar_link"] = self.convert_val(
                "https:" + profile_data['newspaper']["avatar"])
            frec["newspaper_url"] = self.convert_val(
                self.cfgd["data"].erep_url + "/main/newspaper/" +\
                str(profile_data['newspaper']["stripped_title"]) + "-" +\
                str(profile_data['newspaper']["id"]) + "/1")
        return frec

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
            dict: modeled on ST.FriendsFields dataclass
        """
        frec = dict()
        for cnm in ST.FriendsFields.keys():
            frec[cnm] = str(copy(getattr(ST.FriendsFields, cnm)))
        file_nm = "profile_response_{}".format(p_profile_id)
        profile_file = path.abspath(path.join(self.cfgd["data"].log_path,
                                    file_nm))
        if Path(profile_file).exists() and p_use_file:
            with open(profile_file) as pf:
                profile_data = json.loads(pf.read())
            if self.logme:
                msg = "User {} ".format(str(p_profile_id))
                msg += "profile data read from file"
                self.LOG.write_log(ST.LogLevel.DEBUG, msg)
        else:
            profile_url = self.cfgd["data"].erep_url +\
                "/main/citizen-profile-json/" + p_profile_id
            response = requests.get(profile_url)
            if response.status_code == 404:
                msg = "Invalid eRepublik Profile ID."
                raise Exception(ValueError, msg)
            profile_data = json.loads(response.text)
            with open(profile_file, "w") as f:
                f.write(str(response.text))
            if self.logme:
                msg = "User {} ".format(str(p_profile_id))
                msg += "profile data saved to file"
                self.LOG.write_log(ST.LogLevel.DEBUG, msg)

        frec["profile_id"] = p_profile_id
        frec = self.get_basic_citizen_profile(profile_data, frec)
        frec = self.get_citizen_location_data(profile_data, frec)
        frec = self.get_citizen_party_data(profile_data, frec)
        frec = self.get_citizen_military_data(profile_data, frec)
        frec = self.get_citizen_press_data(profile_data, frec)
        return frec

# #######################################################

    def request_friends_data(self, profile_id: str) -> str:
        """Send PM-posting request to eRepublik.

        The PM Posting request will fail due to captcha's.
        But we are really doing this in order to pull in the
         friends list, which shows up in the response.

        Args:
            profile_id (str): citizen ID
        Returns:
            response text
        """
        msg_url = "{}/main/messages-compose/{}".format(self.cfgd["data"].erep_url,
                                                       profile_id)
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
            msg = "friends response code: {}".format(msg_response.status_code)
            self.LOG.write_log(ST.LogLevel.INFO, msg)
        with open(path.abspath(path.join(self.cfgd["data"].log_path,
                                         "friends_response")), "w") as f:
            f.write(msg_response.text)
        return msg_response.text

    def get_friends_data(self, profile_id: str):
        """Get friends list.

        Read local cached copy of previous response if it exists.
        @DEV - make this an option once GUI is in place
        Otherwise make a bogus attempt to send an in-game PM.

        Args:
            profile_id (str): citizen ID, etc.
        """
        friends_file = path.abspath(path.join(self.cfgd["data"].log_path,
                                              "friends_response"))
        if Path(friends_file).exists():
            with open(friends_file) as ff:
                friends_data = ff.read()
        else:
            friends_data = self.request_friends_data(profile_id)
        # parse friends data file or response
        friends_data = friends_data.replace("\t", "").replace("\n", "")
        friends_data = friends_data.split('$j("#citizen_name").tokenInput(')
        friends_data = friends_data[1].split(', {prePopulate:')
        friends_data = json.loads(friends_data[0])

        for friend in friends_data:
            print("Getting profile for {} ... ".format(friend["name"]))
            # eventually, this will be modified to return a dict:s
            frec = self.get_citizen_profile(friend["id"])
            friends_rec = dict()
            for cnm in ST.FriendsRec.keys():
                friends_rec[cnm] = copy(getattr(frec, cnm))
            DB.write_db("add", "friends", friends_rec, None, False)
            time.sleep(.300)

    def set_environment(self):
        """Handle basic set-up as needed.

        Complete necessary set-up steps before proceeding
        """
        self.enable_logging()

        data_rows = DB.query_user(p_decrypt=True)
        if not data_rows:
            id_info, erep_email_id, erep_pass = self.interactive_login_erep()
            self.logout_erep()
            urec = dict()
            for cnm in ST.UserFields.keys():
                urec[cnm] = copy(getattr(ST.UserFields, cnm))
            urec["user_erep_profile_id"] = id_info.profile_id
            urec["user_erep_email"] = erep_email_id
            urec["user_erep_password"] = erep_pass
            urec["encrypt_all"] = False
            DB.write_db("add", "user", urec, None, True)
            frec = self.get_citizen_profile(id_info.profile_id)
            friend_rec = dict()
            for cnm in ST.FriendsFields.keys():
                friend_rec[cnm] = copy(getattr(frec, cnm))
            DB.write_db("add", "friends", friend_rec, None, False)
            time.sleep(1)
            self.login_erep(erep_email_id, erep_pass, False)
            self.get_friends_data(id_info.profile_id)
            self.logout_erep()
        # else:
        #    self.get_friends_data(data_rows[0]["data"].user_erep_profile_id)


    ## XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    ##  Code imported from "erep_messenger"  ###############################

    def send_message(self, profile_data):
        """
        Send message to one recipient

        Dang! --> "The challenge solution was incorrect"

        "sitekey":"6Lf490AUAAAAAIqP0H7DFfXF5tva00u93wxAQ--h"

        See: https://stackoverflow.com/questions/30647113/not-a-robot-recaptcha-without-a-form-but-ajax-instead

        :Args: {string} citizen profile ID - tab - citizen name
        """
        # Prep message
        profile = profile_data.split("\t")
        self.citizen_id = profile[0].strip()
        self.citizen_name = profile[1].strip()
        m_sub = self.subject.get()
        m_body = self.msg_body.get(1.0, tk.END)
        m_body = m_body.replace("[citizen]", self.citizen_name)
        m_body = m_body.replace("[user]", self.user_name)
        # Send message
        msg_url = "https://www.erepublik.com/en/main/messages-compose/{}".format(self.citizen_id)
        msg_headers = {
            "Referer": msg_url,
            "X-Requested-With": "XMLHttpRequest"}
        send_message = {
            "_token": self.erep_csrf_token,
            "citizen_name": self.citizen_id,
            # "citizen_name": self.citizen_name,
            "citizen_subject": m_sub,
            "citizen_message": m_body}

        msg_response = self.erep_rqst.post(
            msg_url, data=send_message, headers=msg_headers, allow_redirects = False)

        self.status_text.config(text = "{}{}".format(self.cfgd["data"].w_txt_sent_to, profile_data))





    def ___set_graphic_interface(self):
        """ Construct GUI widgets for Controls app
        """
        # Window widgets
        self.win_emsg = tk.Tk()     # "root"
        self.win_save = None        # subsidiary
        self.win_load = None        # subsidiary

        self.make_root_emsg_window()
        self.make_menus()
        self.make_status_widgets()
        self.make_profile_ids_editor()
        self.make_message_editor()

    def do_nothing(self):
        """ Used for item separators in menus """
        return True

    def load_list_file(self):
        """
        Read data from selected file and load it into the id_list widget
        """
        id_list_ix = self.id_file_list.curselection()[0]
        id_list = self.listdir_files[id_list_ix]
        with open(path.abspath(path.join(self.app_dir, "db/{}".format(id_list))),
                  "r") as f:
            id_list_data = f.read()
        self.clear_list()
        self.id_list.insert(tk.INSERT, id_list_data)
        self.status_text.config(text = "{}{}".format(self.cfgd["data"].w_txt_file_loaded, id_list))
        self.win_load.withdraw()

    def load_list_dialog(self):
        """
        Populate the profile ids list from a ".list" file stored in the db directory
        @DEV - Eventually replace files with an encrypted sqlite database
        """
        if self.win_load is None:
            self.win_load = tk.Toplevel()
            self.win_load.title(self.cfgd["data"].w_cmd_save_list)
            self.win_load.geometry('400x325+300+200')
            load_frame = ttk.Frame(self.win_load)
            load_frame.grid(row=4, column=2)
            ttk.Label(load_frame, text=self.cfgd["data"].w_cmd_load_list).grid(row=0, column=1)
            ttk.Label(load_frame, text=self.cfgd["data"].s_file_name).grid(row=1, column=1, sticky=tk.W)
            # @DEV - Had trouble getting scroll bars to work as desired
            #   so omitting them for now
            self.id_file_list = tk.Listbox(load_frame, selectmode=tk.SINGLE, width=40)
            self.id_file_list.grid(row=2, column=1)
            ttk.Button(load_frame, text=self.cfgd["data"].s_cancel,
                       command=self.win_load.withdraw).grid(row=4, column=1, sticky=tk.W)
            ttk.Button(load_frame, text=self.cfgd["data"].s_load,
                       command=self.load_list_file).grid(row=4, column=1)
        else:
            self.win_load.deiconify()

        # Load .list file names from db directory
        self.listdir_files =\
            fnmatch.filter(listdir(path.abspath(path.join(self.app_dir, 'db'))), '*.list')
        self.id_file_list.delete(0, self.id_file_list.size())
        for file_nm in self.listdir_files:
            self.id_file_list.insert(self.listdir_files.index(file_nm) + 1, file_nm)

    def save_list_file(self):
        """
        Save the current list of Profile IDs as a file

        @DEV: Note that for pulling text from tk Entry widgets,
               we either define a "textvariable" or just do a .get() with no indexes
        """
        self.current_file_name = self.id_list_file_entry.get()
        self.current_file_name = self.current_file_name.replace(" ", "_").replace("\n", "").replace("'", "_").replace(".list", "").replace(".", "_")
        self.current_file_name = "{}.list".format(self.current_file_name.lower())
        file_path = path.abspath(path.join(self.app_dir, "db/{}".format(self.current_file_name)))
        with open(file_path, "w") as f:
            f.write(self.id_list.get(1.0, tk.END))
        if self.logme:
            self.LOG.write_log(ST.LogLevel.INFO, "Citizens ID .list saved at: {}".format(file_path))

        self.win_save.withdraw()

    def save_list_dialog(self):
        """
        Dialog window for saving the current list of Profile IDs as a file

        @DEV - Run edits / clean-ups on file name and contents once I have them working
        @DEV - "Toplevel" is tk-speak for creating a new window under the root app
        @DEV - After creating it once, we "withdraw" it to close and then "deiconify" to restore
        """
        if self.win_save is None:
            self.win_save = tk.Toplevel()
            self.win_save.title(self.cfgd["data"].w_cmd_save_list)
            self.win_save.geometry('400x125+300+200')
            save_frame = ttk.Frame(self.win_save)
            save_frame.grid(row=3, column=2)
            ttk.Label(save_frame, text=self.cfgd["data"].s_file_name).grid(row=0, column=0, sticky=tk.W)
            self.id_list_file_entry = ttk.Entry(save_frame, width=40)
            if self.current_file_name is not None:
                self.id_list_file_entry.insert(tk.INSERT, self.current_file_name)
            self.id_list_file_entry.grid(row=0, column=1)
            ttk.Button(save_frame, text=self.cfgd["data"].s_cancel,
                       command=self.win_save.withdraw).grid(row=2, column=1, sticky=tk.W)
            ttk.Button(save_frame, text=self.cfgd["data"].s_save,
                       command=self.save_list_file).grid(row=2, column=1)
        else:
            self.win_save.deiconify()

    def clear_list(self):
        """
        Wipe the ID list
        """
        self.id_list.delete(1.0, tk.END)
        self.status_text.config(text = self.cfgd["data"].w_cmd_make_list)

    def clean_list(self):
        """
        Clean up the Profile ID list

        :Return: {string} scrubbed version of the Profile ID List data or False
        """
        # Clean up the list
        list_data_str = self.id_list.get(1.0, tk.END).strip()
        list_data_str = list_data_str.replace(",", "\n").replace("~", "\n").replace("|", "\n")
        list_data_str = list_data_str.replace("\n\n", "\n")
        self.id_list.delete(1.0, tk.END)
        self.id_list.insert(tk.INSERT, list_data_str)

        # Reject if list is empty
        if len(list_data_str) < 1:
            messagebox.showwarning(title = self.cfgd["data"].m_warn_title,
                                   message = self.cfgd["data"].m_bad_list,
                                   detail = "\n{}".format(self.cfgd["data"].m_no_id_list))
            return False
        else:
            return list_data_str

    def verify_list(self):
        """
        Verify the Profile ID list is OK
        """
        self.valid_list = list()
        list_data_str = self.clean_list()
        self.status_text.config(text=self.cfgd["data"].m_verifying_ids)
        if list_data_str:
            # Verify that each ID has a valid profile on eRepublik
            list_data = list_data_str.splitlines()
            for profile_id in list_data:
                if "\t" in profile_id:
                    profile_id = profile_id.split("\t")[0]
                time.sleep(1)
                profile_url = self.cfgd["data"].erep_url + "/main/citizen-profile-json/" + profile_id
                response = requests.get(profile_url)
                # Reject list if it contains an invalid Profile ID
                if response.status_code == 404:
                    messagebox.showwarning(title = self.cfgd["data"].m_warn_title,
                            message = self.cfgd["data"].m_bad_list,
                            detail = "\n{}".format(self.cfgd["data"].m_bad_id.replace("[citizen]", profile_id)))
                    if self.logme:
                        self.LOG.write_log("WARN", "Invalid eRep Profile ID: {}".format(profile_id))
                    return False
                else:
                    # Get current name for Profile ID from eRepublik
                    citizen_profile = json.loads(response.text)
                    self.valid_list.append(profile_id + "\t{}".format(citizen_profile["citizen"]["name"]))
        # Refresh the ID list, showing citizen name along with each profile
        self.status_text.config(text=self.cfgd["data"].m_ids_verified)
        self.id_list.delete(1.0, tk.END)
        self.id_list.insert(tk.INSERT, "\n".join(self.valid_list))
        return True

    def clear_message(self):
        """
        Wipe the Message Subject and Body
        """
        self.subject.delete(0, tk.END)      #Entry object
        self.msg_body.delete(1.0, tk.END)   #Text object

    def verify_message(self):
        """
        Verify the Message Subject and Body are OK
        """
        bad_msg_txt = None
        # Subject (Entry object) empty
        if self.subject is None or len(self.subject.get()) == 0:
            bad_msg_txt = "\n{}".format(self.cfgd["data"].m_no_subject)
        else:
            # Body (Text object) empty
            msg_body_len = len(self.msg_body.get(1.0, tk.END)) - 1
            if self.msg_body is None or msg_body_len < 1:
                bad_msg_txt = "\n{}".format(self.cfgd["data"].m_no_msg_body)
            # Body too long
            elif msg_body_len > 2000:
                bad_msg_txt = "\n{}\n{}{}".format(self.cfgd["data"].m_msg_body_too_long,
                                                self.cfgd["data"].m_msg_body_current_len,
                                                str(msg_body_len))
        if bad_msg_txt is None:
            return True
        else:
            messagebox.showwarning(title = self.cfgd["data"].m_warn_title,
                                   message = self.cfgd["data"].m_bad_message,
                                   detail = bad_msg_txt)
            return False

    def verify_connect(self):
        """
        Make sure there is a connection to eRepublik
        """
        bad_message = False
        bad_msg_txt = ""
        # Not connected to eRepublik
        if self.erep_csrf_token is None:
            bad_message = True
            bad_msg_txt = "\n{}".format(self.cfgd["data"].m_not_logged_in)
        if bad_message:
            messagebox.showwarning(title = self.cfgd["data"].m_warn_title,
                                   message = self.cfgd["data"].m_bad_connect,
                                   detail = bad_msg_txt)
            return False
        else:
            return True

    def verify_all(self):
        """
        Run all the checks before starting to send messages

        :Return: {boolean} False if checks fail else True
        """
        if self.verify_list() \
        and self.verify_message() \
        and self.verify_connect():
            return True
        else:
            return False

    def send_message_to_next(self):
        """
        Attempt to send message to next listed ID
        """
        if self.verify_all():
            self.citizen_ix = 0 if self.citizen_ix is None else self.citizen_ix + 1
            if self.citizen_ix > len(self.valid_list) - 1:
                self.status_text.config(text =\
                    "{} {}".format(self.cfgd["data"].w_txt_list_processed, self.cfgd["data"].w_txt_reload))
            else:
                profile_data = self.valid_list[self.citizen_ix]
                self.send_message(profile_data)

    def send_message_to_all(self):
        """
        Attempt to send message to all listed IDs
        """
        if self.verify_all():
            for profile_data in self.valid_list:
                self.citizen_ix = self.valid_list.index(profile_data)
                self.send_message(profile_data)
                time.sleep(1)

            self.status_text.config(text = self.cfgd["data"].w_txt_list_processed)

    def make_root_emsg_window(self):
        """
        Construct the friends app window
        """
        self.win_ef.title(self.cfgd["data"].w_title)
        self.win_ef.geometry('900x600+100+100')
        self.win_ef.minsize(900,600)

    def make_menus(self):
        """
        Construct the app menus
        """
        menu_bar = tk.Menu(self.win_emsg)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.cfgd["data"].w_file_menu, menu=file_menu)
        file_menu.add_command(label=self.cfgd["data"].w_cmd_load_list, command=self.load_list_dialog)
        file_menu.add_command(label=self.cfgd["data"].w_cmd_save_list, command=self.save_list_dialog)
        file_menu.add_command(label=self.cfgd["data"].w_item_sep, command=self.do_nothing)
        file_menu.add_command(label=self.cfgd["data"].w_cmd_connect, command=self.connect)
        file_menu.add_command(label=self.cfgd["data"].w_cmd_disconnect, command=self.disconnect)
        file_menu.add_command(label=self.cfgd["data"].w_item_sep, command=self.do_nothing)
        file_menu.add_command(label=self.cfgd["data"].w_cmd_exit, command=self.exit_emsg)

        edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.cfgd["data"].w_edit_menu, menu=edit_menu)
        edit_menu.add_command(label=self.cfgd["data"].w_cmd_clear_list, command=self.clear_list)
        edit_menu.add_command(label=self.cfgd["data"].w_cmd_verify_list, command=self.verify_list)
        edit_menu.add_command(label=self.cfgd["data"].w_item_sep, command=self.do_nothing)
        edit_menu.add_command(label=self.cfgd["data"].w_cmd_clear_msg, command=self.clear_message)
        edit_menu.add_command(label=self.cfgd["data"].w_cmd_verify_msg, command=self.verify_message)

        send_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.cfgd["data"].w_send_menu, menu=send_menu)
        send_menu.add_command(label=self.cfgd["data"].w_cmd_send_to_next, command=self.send_message_to_next)
        send_menu.add_command(label=self.cfgd["data"].w_cmd_send_to_all, command=self.send_message_to_all)
        self.win_ef.config(menu=menu_bar)

    def make_status_widgets(self):
        """
        Construct the status message and avatar-display
        """
        status_msg = self.cfgd["data"].w_txt_greet.replace("[user]", self.user_name)
        self.status_text = ttk.Label(self.win_emsg, text=status_msg)
        self.status_text.grid(column=0, row=0)
        tk_img = ImageTk.PhotoImage(self.user_avatar_file)
        user_avatar_img = ttk.Label(self.win_emsg, image=tk_img)
        user_avatar_img.image = tk_img
        user_avatar_img.place(x=725, y=20)

    def make_profile_ids_editor(self):
        """
        Construct frame for listing profile IDs to send messages to
        """
        id_frame = ttk.Frame(self.win_emsg)
        id_frame.grid(row=4, column=0)
        ttk.Label(id_frame, text=self.cfgd["data"].t_id_list_title).pack(side="top")
        scroll_id = ttk.Scrollbar(id_frame)
        scroll_id.pack(side="right", fill="y", expand=False)
        self.id_list = tk.Text(id_frame, height=28, width=40, wrap=tk.WORD, yscrollcommand=scroll_id.set)
        self.id_list.pack(side="left", fill="both", expand=True)
        scroll_id.config(command=self.id_list.yview)

    def make_message_editor(self):
        """
        Construct frame for writing message Subject and Body
        """
        msg_frame = ttk.Frame(self.win_emsg)
        msg_frame.grid(row=4, column=1)
        ttk.Label(msg_frame, text=self.cfgd["data"].t_subject_title).grid(row=0, column=0, sticky=tk.W)
        self.subject = ttk.Entry(msg_frame, width=39)
        self.subject.grid(row=1, column=0)
        ttk.Label(msg_frame, text=self.cfgd["data"].t_body_title).grid(row=2, column=0, sticky=tk.W)
        scroll_msg = ttk.Scrollbar(msg_frame)
        scroll_msg.grid(row=3, column=1, sticky="N,S,W")
        self.msg_body = tk.Text(msg_frame, height=23, width=44, wrap=tk.WORD, yscrollcommand=scroll_msg.set)
        self.msg_body.grid(row=3, column=0, sticky=tk.W)
        scroll_msg.config(command=self.msg_body.yview)
