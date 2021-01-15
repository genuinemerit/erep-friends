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
            DB.write_db('add', 'config', ST.ConfigFields)
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
            return data_rows[0]

    def get_user_data(self):
        """Query data base for most current user record, decrypted

        Returns:
            object  or  bool: False if no result,
                              else dict of "data" and "audit" dataclasses
        """
        data_rows = DB.query_user(p_decrypt=True)
        if len(data_rows) < 1:
            return False
        else:
            return data_rows[0]

    def logout_erep(self):
        """Logout from eRepublik.

        Kind of guessing here. A 302 (redirect) response seems good.
        Redirecting to splash page probably.
        """
        if self.erep_csrf_token is not None:
            formdata = {'_token': self.erep_csrf_token,
                        "remember": '1',
                        'commit': 'Logout'}
            response = self.erep_rqst.post(self.opt.erep_url + "/logout",
                                           data=formdata,
                                           allow_redirects=True)
            if self.logme:
                msg = "logout status code: {}".format(response.status_code)
                self.LOG.write_log(ST.LogLevel.INFO, msg)
            if response.status_code == 302:
                self.erep_csrf_token = None
                response = self.erep_rqst.get(self.opt.erep_url)
                if self.logme:
                    msg = "logout response/redirect text: {}".format(response.text)
                    self.LOG.write_log(ST.LogLevel.INFO, msg)

    def close_controls(self):
        """Close connections. Close the log."""
        if self.erep_csrf_token is not None:
            self.logout_erep()
        try:
            self.LOG.close_logs()
        except Exception:
            pass

    def configure_log(self, log_path, log_level) -> str:
        """Update configs and options with path to log file and log level.

        Args:
            log_path (string) path to parent dir of log file
            log_level (string) key to ST.LogLevel

        """
        self.logme = False
        # Verify values
        if log_path in (None, "None", "") or not Path(log_path).exists():
            msg = "Log file path does not exist." +\
                  "\nUser must create directory or pick a valid one."
            raise Exception(IOError, msg)
        if log_level not in ST.LogLevel.keys():
            msg = "Log level must be one of: {}".format(str(ST.LogLevel.keys))
            raise Exception(ValueError, msg)
        # Update configs
        with open(self.cfg_file_path, "r") as cfgf:
            c_data = cfgf.read()
        cfgf.close()
        c_data_p = c_data.split("log_path = ")
        c_data_pp = c_data_p.split("\n")
        c_data = c_data_p[0] + "'{}'".format(log_path) + c_data_pp[1]
        c_data_p = c_data.split("log_level = ")
        c_data_pp = c_data_p.split("\n")
        c_data = c_data_p[0] + "'{}'".format(log_path) + c_data_pp[1]
        with open(self.cfg_file_path, "w") as cfgf:
            cfgf.write(c_data)
        cfgf.close()
        self.set_options(self.cfg_file_path)

# #######################################################



    def enable_logging(self):
        """Assign log file location. Instantiate Logger object."""

        self.logme = False if self.opt.log_level == ST.LogLevel.NOTSET\
                            else True

        log_file = path.join(self.opt.log_path, self.opt.log_name)
        self.LOG = Logger(log_file, self.opt.log_level)
        self.LOG.set_log()
        if self.logme:
            msg = "Log file location: {}".format(log_file)
            self.LOG.write_log(ST.LogLevel.INFO, msg)
            msg = "Log level: {}".format(self.opt.log_level)
            self.LOG.write_log(ST.LogLevel.INFO, msg)

    def set_backup_db_path(self) -> str:
        """Set path to backup database.

        No scheduled backups yet. Do backups on demand.
        No rolling backups. A single backup db overwritten whenever
         a backup is taken.
        Suitable to use as recovery for main db by simply copying
         the backup file to the main db location.
        @DEV
            Replace CLI input with a GUI

        Returns:
            string: full parent path to backup db or 'None'
        """
        db_path = ST.ConfigFields.bkup_db_path
        while db_path in (None, "None", ""):
            print("\nEnter backup location or 'n':")
            db_path = input()
        if db_path[:1].lower() != 'n':
            db_path = path.abspath(path.realpath(db_path))
            if not Path(db_path).exists():
                mkdir(db_path)
        return db_path

    def set_archive_db_path(self) -> str:
        """Set path to archive database.

        This is where we take a db copy prior to running a purge.
        @DEV
            Replace CLI input with a GUI

        Returns:
            string: full parent path to archive db or 'None'
        """
        db_path = ST.ConfigFields.arcv_db_path
        while db_path in (None, "None", ""):
            print("\nEnter archive DB location or 'n':")
            db_path = input()
        if db_path[:1].lower() != 'n':
            db_path = path.abspath(path.realpath(db_path))
            if not Path(db_path).exists():
                mkdir(db_path)
        return db_path



    def get_local_login_file(self):
        """Use local copy of login response if available.

        Returns:
            text or bool: full response.text from eRep login GET  or  False
        """
        login_file = path.abspath(path.join(self.opt.log_path,
                                            "login_response"))
        response_text = False
        if Path(login_file).exists():
            with open(login_file) as lf:
                response_text = lf.read()
                lf.close()
        return response_text



    def get_token(self, response_text: str):
        """Get/save CSRF token.

        Args:
            response_text (string): full response text from eRep login GET
        """
        parse_text = response_text.split("var csrfToken = '")
        parse_text = parse_text[1].split("';")
        self.erep_csrf_token = parse_text[0]

    def login_erep(self, p_email: str, p_password: str,
                   p_save_response: bool) -> str:
        """Login to eRepublik to confirm credentials and get profile ID.

        Args:
            p_email (str): User login email address
            p_password (str): User login password
            p_save_response (bool): If True, store response text as a file

        Returns:
            text: full response.text from eRep login GET  or  None
        """
        formdata = {'citizen_email': p_email,
                    'citizen_password': p_password,
                    "remember": '1', 'commit': 'Login'}
        response = self.erep_rqst.post(self.opt.erep_url + "/login",
                                       data=formdata,
                                       allow_redirects=False)
        if self.logme:
            msg = "login status code: {}".format(response.status_code)
            self.LOG.write_log(ST.LogLevel.INFO, msg)
        if p_save_response:
            with open(path.abspath(path.join(self.opt.log_path,
                                                "login_response")), "w") as f:
                f.write(response.text)
        if response.status_code == 302:
            response = self.erep_rqst.get(self.opt.erep_url)
            self.get_token(response.text)
        else:
            # Don't understand yet why sometimes I get a 200 response
            #  when I'd been getting 302 for a while. The 200 response
            #  basically means the login didn't work and it is still
            #  sitting there on the login page.  The response is such
            #  a jumble of javascript it is hard to see what is really
            #  being presented. But there seems to be at least the
            #  possibility that a captcha is being used sometimes.
            # Maybe that is random. Or maybe if it has notice a lot
            #  of activity from my IP recently that seems to indicate
            #  a script is being used?  Seems like when I've seen this
            #  before I just had to wait several hours and then it started
            #  working OK again.
            msg = "Login connection failed. See response text in log." +\
                  "\n Probably a captcha. May want to wait a few hours."
            raise Exception(ConnectionError, msg)
        return response.text

    def get_user_info(self, response_text: str):
        """Extract ID and name from response text.

        Args:
            response_text (string): full response text from eRep login GET

        Returns:
            namedtuple: id_info.. profile_id, user_name

        This shows up about line 41 of the response text:
        {"citizenId":9194827,"isOrganization":0,"isAdult":true,"country":24,"citizenshipCountryId":24,"name":"RF Williams","avatar":"https://cdnt.erepublik.net/tSSiPU1zChZhwB6TromFPARPJrQ=/55x55/smart/avatars/Citizens/2017/05/04/0aff92a6d29c160c51d5843f6a445c01.png?fad2c777d8f3f833ce09201bd7f8bb2c"

        This shows up in the login response text too, but much further down.
        Since I'll grab this info and more from the profile later on, just go for the earlier
        instance of ID and Name here.

        citizenInfo: {"id":9194827,"name":"RF Williams","sex":"M","created_at":"2017-05-04 17:29:03","is_organization":0,"is_alive":1,"is_validated":1,"has_avatar":1,"parent_id":0,"is_payer":0,"has_jid":1,"avatar_version":"fad2c777d8f3f833ce09201bd7f8bb2c","avatar_file":"png","level":52,"avatar":"https://cdnt.erepublik.net/tSSiPU1zChZhwB6TromFPARPJrQ=/55x55/smart/avatars/Citizens/2017/05/04/0aff92a6d29c160c51d5843f6a445c01.png?fad2c777d8f3f833ce09201bd7f8bb2c","profile_url":"//m.erepublik.com/en/citizen/profile/9194827"},
        """
        # print("login response_text: {}".format(response_text))

        id_info = namedtuple("id_info", "profile_id user_name")
        # Get user profile ID.
        parse_text = response_text.split('"citizen":{"citizenId":')
        parse_text = parse_text[1].split(",")
        id_info.profile_id = parse_text[0]
        # Get user name.
        parse_text = response_text.split('"name":')
        parse_text = parse_text[1].split(",")
        id_info.user_name = parse_text[0].replace('"', '')

        if self.logme and self.opt.log_level == 'DEBUG':
            msg = "CSRF Token:\t{}".format(self.erep_csrf_token)
            self.LOG.write_log(ST.LogLevel.INFO, msg)
            msg = "Login response:\n{}".format(response_text)
            self.LOG.write_log(ST.LogLevel.INFO, msg)
        return id_info

    def interactive_login_erep(self) -> tuple:
        """Connect to eRepublik using valid email and password.

        Returns:
            tuple: (namedtuple: id_info, erep_mail_id, erep_pass)
        """
        if self.erep_csrf_token is not None:
            msg = "Already logged in.\nRun logout method."
            raise Exception(ConnectionError, msg)
        else:
            # Establish if user credentials work
            # Replace with data from user record if it exists
            print("\nEnter eRepublik Email Login ID and Password to enable"
                  " gathering full friends list.")
            print("Password won't display on the screen."
                  " Both Email and Password are stored encrypted.")
            erep_email_id = input("eRep Email Login ID: ")
            erep_pass = getpass.getpass("eRep Password: ")
            response_text = self.get_local_login_file()
            if response_text:
                if self.logme:
                    msg = "Using cached login data for credentials"
                    self.LOG.write_log(ST.LogLevel.INFO, msg)
            else:
                response_text = self.login_erep(erep_email_id,
                                                erep_pass, True)
                if not response_text:
                    if not response_text:
                        msg = "Login failed.\nCheck credentials."
                        raise Exception(ConnectionError, msg)
            id_info = self.get_user_info(response_text)
            return (id_info, erep_email_id, erep_pass)

    def get_user_profile(self, profile_id: str):
        """Retrieve profile for user from eRepublik.

        Get the user's eRepublik profile ID from config file.
        Set the user name and grab the user's avatar file.

        Args:
            profile_id (str): citizen ID

        Raises:
            ValueError if profile ID returns 404 from eRepublik

        Returns:
            dataclass instance: ST.ControlsFields
        """
        file_nm = "profile_response_{}".format(profile_id)
        profile_file = path.abspath(path.join(self.opt.log_path, file_nm))
        if Path(profile_file).exists():
            with open(profile_file) as pf:
                profile_data = json.loads(pf.read())        # convert to dict
        else:
            profile_url = self.opt.erep_url +\
                "/main/citizen-profile-json/" + profile_id
            response = requests.get(profile_url)       # returns JSON
            if response.status_code == 404:
                msg = "Invalid eRepublik Profile ID."
                raise Exception(ValueError, msg)
            profile_data = json.loads(response.text)   # convert to dict
            with open(profile_file, "w") as f:
                f.write(str(response.text))            # save a copy

        f_rec = ST.ControlsFields
        f_rec.profile_id = profile_id
        f_rec.name = profile_data["citizen"]["name"]
        f_rec.is_alive = profile_data["citizen"]["is_alive"]
        f_rec.is_adult = profile_data["isAdult"]
        f_rec.avatar_link = profile_data["citizen"]["avatar"]
        f_rec.level = profile_data["citizen"]["level"]
        f_rec.xp =\
            profile_data["citizenAttributes"]["experience_points"]
        f_rec.friends_count = profile_data["friends"]["number"]
        f_rec.achievements_count = len(profile_data["achievements"])
        f_rec.is_in_congress = profile_data['isCongressman']
        f_rec.is_ambassador = profile_data['isAmbassador']
        f_rec.is_dictator = profile_data['isDictator']
        f_rec.is_country_president = profile_data['isPresident']
        f_rec.is_top_player = profile_data['isTopPlayer']
        f_rec.is_party_member = profile_data["isPartyMember"]
        f_rec.is_party_president = profile_data["isPartyPresident"]

        f_rec.citizenship_country =\
            profile_data["location"]["citizenshipCountry"]["name"]

        if not isinstance(profile_data["military"], bool)\
          and not isinstance(profile_data["military"]["militaryData"], bool):
            f_rec.aircraft_rank =\
                profile_data['military']['militaryData']["aircraft"]["name"]
            f_rec.ground_rank =\
                profile_data['military']['militaryData']["ground"]["name"]

        if "residenceCity" in profile_data.keys():
            f_rec.residence_city =\
                profile_data["city"]["residenceCity"]["name"]
            f_rec.residence_region =\
                profile_data["city"]["residenceCity"]["region_name"]
            f_rec.residence_country =\
                profile_data["city"]["residenceCity"]["country_name"]

        if "partyData" in profile_data.keys()\
          and profile_data["partyData"] != []\
          and not isinstance(profile_data["partyData"], bool)\
          and not isinstance(profile_data["partyData"], str):
            f_rec.party_name = str(profile_data["partyData"]["name"])
            f_rec.party_avatar_link =\
                "https:" + profile_data["partyData"]["avatar"]
            f_rec.party_orientation =\
                profile_data["partyData"]["economical_orientation"]
            f_rec.party_url = self.opt.erep_url + "/party/" +\
                str(profile_data["partyData"]["stripped_title"]) + "-" +\
                str(profile_data["partyData"]["id"]) + "/1"

        if "militaryUnit" in profile_data["military"].keys()\
          and not isinstance(profile_data["military"], bool)\
          and not isinstance(profile_data["military"]["militaryUnit"], bool):
            f_rec.militia_name =\
                str(profile_data['military']['militaryUnit']['name'])
            f_rec.military_rank =\
                profile_data['military']['militaryUnit']["militaryRank"]
            f_rec.militia_url = self.opt.erep_url +\
                "/military/military-unit/" +\
                str(profile_data['military']['militaryUnit']['id']) +\
                "/overview"
            f_rec.militia_size =\
                profile_data['military']['militaryUnit']['member_count']
            f_rec.militia_avatar_link =\
                "https:" + profile_data['military']['militaryUnit']["avatar"]

        if "newspaper" in profile_data.keys()\
          and not isinstance(profile_data['newspaper'], bool):
            f_rec.newspaper_name =\
                str(profile_data['newspaper']['name'])
            f_rec.newspaper_avatar_link =\
                "https:" + profile_data['newspaper']["avatar"]
            f_rec.newspaper_url = self.opt.erep_url + "/main/newspaper/" +\
                str(profile_data['newspaper']["stripped_title"]) + "-" +\
                str(profile_data['newspaper']["id"]) + "/1"

        # Cast to string and remove embedded apostrophes.
        for field in ST.FIELDS["friends"]:
            val = str(getattr(f_rec, field)).replace("'", "_")
            setattr(f_rec, field, val)

        if self.logme and self.opt.log_level == ST.LogLevel.DEBUG:
            msg = "user_profile: {}".format(profile_data)
            self.LOG.write_log(ST.LogLevel.DEBUG, msg)
        return f_rec

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
        msg_url = "{}/main/messages-compose/{}".format(self.opt.erep_url,
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
        with open(path.abspath(path.join(self.opt.log_path,
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
        friends_file = path.abspath(path.join(self.opt.log_path,
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
            f_rec = self.get_user_profile(friend["id"])
            DB.write_db("add", "friends", f_rec, None, False)
            time.sleep(.300)

    def set_environment(self):
        """Handle basic set-up as needed.

        Complete necessary set-up steps before proceeding
        """
        self.enable_logging()

        data_rows = DB.query_user(p_decrypt=True)
        if len(data_rows) < 1:
            id_info, erep_email_id, erep_pass = self.interactive_login_erep()
            self.logout_erep()
            u_row = ST.UserFields
            u_row.user_erep_profile_id = id_info.profile_id
            u_row.user_erep_email = erep_email_id
            u_row.user_erep_password = erep_pass
            u_row.encrypt_all = 'False'
            DB.write_db("add", "user", u_row, None, True)
            f_rec = self.get_user_profile(id_info.profile_id)
            DB.write_db("add", "friends", f_rec, None, False)
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
        pp(msg_response.status_code)
        pp(msg_response.text)

        self.status_text.config(text = "{}{}".format(self.opt.w_txt_sent_to, profile_data))





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
        self.status_text.config(text = "{}{}".format(self.opt.w_txt_file_loaded, id_list))
        self.win_load.withdraw()

    def load_list_dialog(self):
        """
        Populate the profile ids list from a ".list" file stored in the db directory
        @DEV - Eventually replace files with an encrypted sqlite database
        """
        if self.win_load is None:
            self.win_load = tk.Toplevel()
            self.win_load.title(self.opt.w_cmd_save_list)
            self.win_load.geometry('400x325+300+200')
            load_frame = ttk.Frame(self.win_load)
            load_frame.grid(row=4, column=2)
            ttk.Label(load_frame, text=self.opt.w_cmd_load_list).grid(row=0, column=1)
            ttk.Label(load_frame, text=self.opt.s_file_name).grid(row=1, column=1, sticky=tk.W)
            # @DEV - Had trouble getting scroll bars to work as desired
            #   so omitting them for now
            self.id_file_list = tk.Listbox(load_frame, selectmode=tk.SINGLE, width=40)
            self.id_file_list.grid(row=2, column=1)
            ttk.Button(load_frame, text=self.opt.s_cancel,
                       command=self.win_load.withdraw).grid(row=4, column=1, sticky=tk.W)
            ttk.Button(load_frame, text=self.opt.s_load,
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
            self.win_save.title(self.opt.w_cmd_save_list)
            self.win_save.geometry('400x125+300+200')
            save_frame = ttk.Frame(self.win_save)
            save_frame.grid(row=3, column=2)
            ttk.Label(save_frame, text=self.opt.s_file_name).grid(row=0, column=0, sticky=tk.W)
            self.id_list_file_entry = ttk.Entry(save_frame, width=40)
            if self.current_file_name is not None:
                self.id_list_file_entry.insert(tk.INSERT, self.current_file_name)
            self.id_list_file_entry.grid(row=0, column=1)
            ttk.Button(save_frame, text=self.opt.s_cancel,
                       command=self.win_save.withdraw).grid(row=2, column=1, sticky=tk.W)
            ttk.Button(save_frame, text=self.opt.s_save,
                       command=self.save_list_file).grid(row=2, column=1)
        else:
            self.win_save.deiconify()

    def clear_list(self):
        """
        Wipe the ID list
        """
        self.id_list.delete(1.0, tk.END)
        self.status_text.config(text = self.opt.w_cmd_make_list)

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
            messagebox.showwarning(title = self.opt.m_warn_title,
                                   message = self.opt.m_bad_list,
                                   detail = "\n{}".format(self.opt.m_no_id_list))
            return False
        else:
            return list_data_str

    def verify_list(self):
        """
        Verify the Profile ID list is OK
        """
        self.valid_list = list()
        list_data_str = self.clean_list()
        self.status_text.config(text=self.opt.m_verifying_ids)
        if list_data_str:
            # Verify that each ID has a valid profile on eRepublik
            list_data = list_data_str.splitlines()
            for profile_id in list_data:
                if "\t" in profile_id:
                    profile_id = profile_id.split("\t")[0]
                time.sleep(1)
                profile_url = self.opt.erep_url + "/main/citizen-profile-json/" + profile_id
                response = requests.get(profile_url)
                # Reject list if it contains an invalid Profile ID
                if response.status_code == 404:
                    messagebox.showwarning(title = self.opt.m_warn_title,
                            message = self.opt.m_bad_list,
                            detail = "\n{}".format(self.opt.m_bad_id.replace("[citizen]", profile_id)))
                    if self.logme:
                        self.LOG.write_log("WARN", "Invalid eRep Profile ID: {}".format(profile_id))
                    return False
                else:
                    # Get current name for Profile ID from eRepublik
                    citizen_profile = json.loads(response.text)
                    self.valid_list.append(profile_id + "\t{}".format(citizen_profile["citizen"]["name"]))
        # Refresh the ID list, showing citizen name along with each profile
        self.status_text.config(text=self.opt.m_ids_verified)
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
            bad_msg_txt = "\n{}".format(self.opt.m_no_subject)
        else:
            # Body (Text object) empty
            msg_body_len = len(self.msg_body.get(1.0, tk.END)) - 1
            if self.msg_body is None or msg_body_len < 1:
                bad_msg_txt = "\n{}".format(self.opt.m_no_msg_body)
            # Body too long
            elif msg_body_len > 2000:
                bad_msg_txt = "\n{}\n{}{}".format(self.opt.m_msg_body_too_long,
                                                self.opt.m_msg_body_current_len,
                                                str(msg_body_len))
        if bad_msg_txt is None:
            return True
        else:
            messagebox.showwarning(title = self.opt.m_warn_title,
                                   message = self.opt.m_bad_message,
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
            bad_msg_txt = "\n{}".format(self.opt.m_not_logged_in)
        if bad_message:
            messagebox.showwarning(title = self.opt.m_warn_title,
                                   message = self.opt.m_bad_connect,
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
                    "{} {}".format(self.opt.w_txt_list_processed, self.opt.w_txt_reload))
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

            self.status_text.config(text = self.opt.w_txt_list_processed)

    def make_root_emsg_window(self):
        """
        Construct the friends app window
        """
        self.win_ef.title(self.opt.w_title)
        self.win_ef.geometry('900x600+100+100')
        self.win_ef.minsize(900,600)

    def make_menus(self):
        """
        Construct the app menus
        """
        menu_bar = tk.Menu(self.win_emsg)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.opt.w_file_menu, menu=file_menu)
        file_menu.add_command(label=self.opt.w_cmd_load_list, command=self.load_list_dialog)
        file_menu.add_command(label=self.opt.w_cmd_save_list, command=self.save_list_dialog)
        file_menu.add_command(label=self.opt.w_item_sep, command=self.do_nothing)
        file_menu.add_command(label=self.opt.w_cmd_connect, command=self.connect)
        file_menu.add_command(label=self.opt.w_cmd_disconnect, command=self.disconnect)
        file_menu.add_command(label=self.opt.w_item_sep, command=self.do_nothing)
        file_menu.add_command(label=self.opt.w_cmd_exit, command=self.exit_emsg)

        edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.opt.w_edit_menu, menu=edit_menu)
        edit_menu.add_command(label=self.opt.w_cmd_clear_list, command=self.clear_list)
        edit_menu.add_command(label=self.opt.w_cmd_verify_list, command=self.verify_list)
        edit_menu.add_command(label=self.opt.w_item_sep, command=self.do_nothing)
        edit_menu.add_command(label=self.opt.w_cmd_clear_msg, command=self.clear_message)
        edit_menu.add_command(label=self.opt.w_cmd_verify_msg, command=self.verify_message)

        send_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.opt.w_send_menu, menu=send_menu)
        send_menu.add_command(label=self.opt.w_cmd_send_to_next, command=self.send_message_to_next)
        send_menu.add_command(label=self.opt.w_cmd_send_to_all, command=self.send_message_to_all)
        self.win_ef.config(menu=menu_bar)

    def make_status_widgets(self):
        """
        Construct the status message and avatar-display
        """
        status_msg = self.opt.w_txt_greet.replace("[user]", self.user_name)
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
        ttk.Label(id_frame, text=self.opt.t_id_list_title).pack(side="top")
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
        ttk.Label(msg_frame, text=self.opt.t_subject_title).grid(row=0, column=0, sticky=tk.W)
        self.subject = ttk.Entry(msg_frame, width=39)
        self.subject.grid(row=1, column=0)
        ttk.Label(msg_frame, text=self.opt.t_body_title).grid(row=2, column=0, sticky=tk.W)
        scroll_msg = ttk.Scrollbar(msg_frame)
        scroll_msg.grid(row=3, column=1, sticky="N,S,W")
        self.msg_body = tk.Text(msg_frame, height=23, width=44, wrap=tk.WORD, yscrollcommand=scroll_msg.set)
        self.msg_body.grid(row=3, column=0, sticky=tk.W)
        scroll_msg.config(command=self.msg_body.yview)
