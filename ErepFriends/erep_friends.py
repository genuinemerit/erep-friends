#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Module:    erep_friends.py
Class:     ErepFriends/0  inherits object
Author:    PQ <pq_rfw @ pm.me>
"""
import fnmatch
import getpass
import json
import logging
import re
import sys
import time
from collections import namedtuple
from os import listdir, mkdir, path

import requests
import tkinter as tk
from bs4 import BeautifulSoup as bs
from erepublik import Citizen, constants, utils
from pathlib import Path
from PIL import Image, ImageTk
from pprint import pprint as pp        # noqa: F401
from pytz import all_timezones
from tkinter import messagebox, ttk
from tornado.options import define, options

from gm_dbase import GmDbase
from gm_logger import GmLogger
from gm_reference import GmReference

GR = GmReference()

class ErepFriends(object):
    """
    Friends list manager for eRepublik
    """
    def __init__(self):
        """ Initialize ErepFriends object """
        self.__set_environment()

        """
        self.__set_erepublik()

        # This is in-memory text and scrub
        # Maybe want to separate this from pure GUI logic
        self.id_list = None
        self.status_text = None
        self.citizen_id = None
        self.citizen_name = None
        self.citizen_ix = None
        self.id_list_file_entry = None
        self.id_file_list = None
        self.valid_list = None
        # This is message data:
        self.subject = None
        self.msg_body = None

        # This is sort of IO/database/filtering stuff
        # Can replace files with views? Dynamically?
        self.listdir_files = None
        self.current_file_name = 'profile_ids'

        # Construct and launch the GUI
        self.___set_graphic_interface()
        """

    def __repr__(self):
        """ Print description of class
            TODO once code settles down
        """
        pass

    def __create_config_file(self, p_cfg_file_path: str):
        """ Define and create config file

        Args:
            p_cfg_file_path (string): full path to config file
        """
        cfg_txt = ""
        for cfg_nm, cfg_val in GR.configs.items():
            cfg_txt += "{} = '{}'\n".format(cfg_nm, cfg_val)
        with open(p_cfg_file_path, 'w') as cfgf:
            cfgf.write(cfg_txt)
        cfgf.close()

    def __set_options(self, p_cfg_file_path: str):
        """ Get login info and other settings from config file.

            Args:
                p_cfg_file_path (string): full path to config file

            Sets:
                self.opt (namedtuple): name.value of all options
        """
        self.opt = None
        opt_names = [
            'db_name',
            'data_path', 'bkup_db_path', 'arcv_db_path',
            'log_path', 'log_level', 'log_name', 'local_tz',
            'erep_url',
            'w_txt_title', 'w_txt_greet',
            'w_txt_connected', 'w_txt_disconnected',
            'w_txt_login_failed']
        for opt_nm in opt_names:
            define(opt_nm)
        options.parse_config_file(p_cfg_file_path)
        self.opt = options

    def __configure_database(self):
        """ Configure DB object and create databases
              if main DB does not already exist.

            Sets:
                self.DB (object): instantiates GmDbase class
        """
        self.DB = GmDbase()
        self.DB.config_db(self.opt.db_name, self.opt.data_path,
                          self.opt.bkup_db_path, self.opt.arcv_db_path)
        main_db_file =\
            path.join(self.opt.data_path, self.opt.db_name)
        if not Path(main_db_file).exists():
            self.DB.create_db()

    def __enable_logging(self):
        """ Assign log file location

            Sets:
                self.LOG (object): instance of GmLogger class
        """
        self.logme = False
        if self.opt.log_path not in (None, "None", ""):
            log_level = self.opt.log_level
            log_name = self.opt.log_name
            self.logme = True if log_level in list(GR.LOGLEVEL.keys())\
                              else False
            log_file =\
                path.join(self.opt.log_path, self.opt.log_name)
            self.LOG = GmLogger(log_file, log_level, self.opt.local_tz)
            self.LOG.set_logs()
            if self.logme:
                self.LOG.write_log("INFO",
                                   "Log file location: {}".format(log_file))
                self.LOG.write_log("INFO",
                                   "Log level: {}".format(log_level))

    def __set_environment(self):
        """ Handle basic set-up as needed.
            Complete necessary set-up steps before proceeding
        @DEV
            Provide explain/help  of what goes on here.
            Optional files can also be set up later if desired.
            Replace console inputs with GUI.


        if not sys.version_info >= (3, 6):
            raise AssertionError('This script requires Python version 3.6 and higher\n'
                                 'But Your version is v{}.{}.{}'.format(*sys.version_info))
        """
        if sys.version_info[0] < 3:
            raise Exception("Python 3 is required.")

        data_path = path.abspath(path.realpath(GR.configs["data_path"]))
        if not Path(data_path).exists():
            mkdir(data_path)

        cfg_file_path = path.join(data_path, GR.configs["cfg_file_name"])
        if not Path(cfg_file_path).exists():
            self.set_backup_db_path()
            self.set_archive_db_path()
            self.set_local_time_zone()
            self.set_log_file_path()
            self.__create_config_file(cfg_file_path)
        self.__set_options(cfg_file_path)
        self.__configure_database()
        self.__enable_logging()

        # Establish user profile data and credentials
        #   All of this will move to a standalone method or two...

        # 1. See if user exists and get their profile data
        #    Later, we'll use this to populate a friends record
        result = self.DB.query_db("user")
        if result.rowcount == -1:
            # User not found on database, so set up user profile and credentials
            print("\nEnter user's eRepublik Profile ID to gather user info from eRepublik.")
            erep_profile_id = input("eRep Profile ID: ")
            erep_profile_id = erep_profile_id.strip()
            profile_rec = self.get_user_profile(erep_profile_id)
            for field in profile_rec._fields:
                print("{}: {}".format(field, getattr(profile_rec, field)))

            # 2. Establish that the user credentials work
            print("\nEnter the user's eRepublik ID and Password to enable gathering full friends list.")
            print("Password won't display on the screen. Both ID and Password are stored encrypted.")
            erep_email_id = input("eRep Email Login ID: ")
            erep_pass = getpass.getpass("eRep Password: ")

            # pp((erep_email_id, erep_pass))

            # 3. Attempt to log into eRepublik
            #  So this seems to work fine, but not entirely clear what is returned
            #  Looking thru his code, I do NOT see any function for returning the friends list
            #  It also seems to "report" a lot of activity to ?? Telegram, maybe emails.
            #  Writes to log pretty often but not sure where that log is located.
            #  Not so sure I like that!
            #  This is mainly about doing a lot of stuff using a script.
            #  I don't see any "logout" or "disconnect". There is a note about
            #  returning to home page after 15 minutes of inactivity.
            player = Citizen(email=erep_email_id, password=erep_pass, auto_login=True)

            print(player)
            pp(player)
            dir(player)

        """

class ErepublikProfileAPI(CitizenBaseAPI):

    >> requires being logged in:
    def _get_main_citizen_hovercard(self, citizen_id: int) -> Response:
        return self.get(f"{self.url}/main/citizen-hovercard/{citizen_id}")

    >> does not require being logged in:
    def _get_main_citizen_profile_json(self, citizen_id: int) -> Response:
        return self.get(f"{self.url}/main/citizen-profile-json/{citizen_id}")

    def _get_main_party_members(self, party_id: int) -> Response:
        return self.get(f"{self.url}/main/party-members/{party_id}")

    def _post_login(self, email: str, password: str) -> Response:
        data = dict(csrf_token=self.token, citizen_email=email, citizen_password=password, remember='on')
        return self.post(f"{self.url}/login", data=data)

    def _post_main_party_post_create(self, body: str) -> Response:
        data = {"_token": self.token, "post_message": body}
        return self.post(f"{self.url}/main/party-post/create/json", data=data)

    def _post_main_wall_post_create(self, body: str) -> Response:
        data = {"_token": self.token, "post_message": body}
        return self.post(f"{self.url}/main/wall-post/create/json", data=data)

    def _get_main_city_data_residents(self, city_id: int, page: int = 1, params: Mapping[str, Any] = None) -> Response:
        if params is None:
            params = {}
        return self.get(f"{self.url}/main/city-data/{city_id}/residents", params={"currentPage": page, **params})


    class ErepublikProfileAPI(CitizenBaseAPI):

    def _post_main_messages_compose(self, subject: str, body: str, citizens: List[int]) -> Response:
        url_pk = 0 if len(citizens) > 1 else str(citizens[0])
        data = dict(citizen_name=",".join([str(x) for x in citizens]),
                    citizen_subject=subject, _token=self.token, citizen_message=body)
        return self.post(f"{self.url}/main/messages-compose/{url_pk}", data=data)


class CitizenMedia(BaseCitizen):

    def publish_article(self, title: str, content: str, kind: int) -> int:
        kinds = {1: "First steps in eRepublik", 2: "Battle orders", 3: "Warfare analysis",
                 4: "Political debates and analysis", 5: "Financial business",
                 6: "Social interactions and entertainment"}
        if kind in kinds:
            data = {'title': title, 'content': content, 'country': self.details.citizenship.id, 'kind': kind}
            resp = self._post_main_write_article(title, content, self.details.citizenship.id, kind)
            try:
                article_id = int(resp.history[1].url.split("/")[-3])
                self._report_action("ARTICLE_PUBLISH", f"Published new article \"{title}\" ({article_id})", kwargs=data)
            except:  # noqa
                article_id = 0
            return article_id
        else:
            kinds = "\n".join([f"{k}: {v}" for k, v in kinds.items()])
            raise classes.ErepublikException(f"Article kind must be one of:\n{kinds}\n'{kind}' is not supported")



    def get_mu_members(self, mu_id: int) -> Dict[int, str]:
        ret = {}
        r = self._get_military_unit_data(mu_id)

        for page in range(int(r.json()["panelContents"]["pages"])):
            r = self._get_military_unit_data(mu_id, currentPage=page + 1)
            for user in r.json()["panelContents"]["members"]:
                if not user["isDead"]:
                    ret.update({user["citizenId"]: user["name"]})
        return ret


        """


            # 5. If credentials are OK (login works and profile IDs match), then:

                # 6. Generate encryption key for the user
                # 7. Ask if they want to encrypt all records

                # 8. Generate uid and hash_id for user record
                # 9. Write user record
                # 10. Generate uid and hash_id for friend record
                # 11. Write friends record for the user
        else:
            # User records found on DB. May need to check that they are correct, and/
            # or provide an option to refresh them (e.g., new password, new mail id)
            for row in result:
                pp(row)

    def set_backup_db_path(self):
        """ Set path to backup database.
            No scheduled backups yet. Do backups on demand.
            No rolling backups. A single backup db overwritten whenever
              a backup is taken.
            Suitable to use as recovery for main db by simply copying
              the backup file to the main db location.
            @DEV
                Replace CLI input with a GUI
        """
        db_path = GR.configs["bkup_db_path"]
        while db_path in (None, "None", ""):
            print("\nEnter location for Backup database or 'n' for no backups:")
            db_path = input()
        if db_path[:1].lower() != 'n':
            db_path = path.abspath(path.realpath(db_path))
            if not Path(db_path).exists():
                mkdir(db_path)

    def set_archive_db_path(self):
        """ Set path to archive database.
            This is where we take a db copy prior to running a purge.
            @DEV
                Replace CLI input with a GUI
        """
        db_path = GR.configs["arcv_db_path"]
        while db_path in (None, "None", ""):
            print("\nEnter location for Archive database or 'n' for no purge/archive:")
            db_path = input()
        if db_path[:1].lower() != 'n':
            db_path = path.abspath(path.realpath(db_path))
            if not Path(db_path).exists():
                mkdir(db_path)

    def set_local_time_zone(self):
        """ Since it is difficult (for me!) to get localhost time zone in
             POSIX/Olson format, ask user to input it.  This has little effect
             on anything, just to display it in log session header.
            @DEV
                Replace CLI input with a GUI
        """
        local_tz = GR.configs["local_tz"]
        while local_tz in (None, "None", ""):
            print("\nEnter localhost Time Zone in POSIX/Olson format or 'n' to skip it:")
            local_tz = input()
            if local_tz not in all_timezones:
                print("\n{} is not a valid Time Zone name.".format(local_tz))
                print(  "Try again or 'n' to skip it.")
                local_tz = ""
        if local_tz in all_timezones:
            GR.configs["local_tz"] = local_tz
            GR.LOCAL_TZ = local_tz

    def set_log_file_path(self):
        """ Set path to log file.
            No rolling log mechanism in place yet.
            Manually backup or delete logs if desired.
            As long as log file path and name are defined,
              system creates a new log file if needed.
            @DEV
                Replace CLI input with a GUI
        """
        log_path = GR.configs["log_path"]
        while log_path in (None, "None", ""):
            print("\nEnter location for Log file or 'n' for no logs:")
            log_path = input()
        if log_path[:1].lower() != 'n':
            log_path = path.abspath(path.realpath(log_path))
            if not Path(log_path).exists():
                mkdir(log_path)

    def get_user_profile(self, p_profile_id: str) -> GR.NamedTuple:
        """ Retrieve profile for user from eRepublik.
            Get the user's eRepublik profile ID from config file.
            Set the user name and grab the user's avatar file.

        Args:
            p_profile_id (string): a valid eRepublik user profile ID

        Raises:
            ValueError if profile ID returns 404 from eRepublik

        Returns:
            namedtuple: GR.friends_rec
        """
        # This is pretty sweet and simple.
        # See if erepublik library can do any better...
        profile_url = self.opt.erep_url + "/main/citizen-profile-json/" + p_profile_id
        erep_response = requests.get(profile_url)       # returns JSON
        if erep_response.status_code == 404:
            raise Exception(ValueError, "Invalid eRepublik Profile ID.")

        profile_data = json.loads(erep_response.text)   # convert to dict
        profile_rec = GR.friends_rec

        profile_rec.uid = None

        profile_rec.profile_id = p_profile_id
        profile_rec.name = profile_data["citizen"]["name"]
        profile_rec.is_alive = profile_data["citizen"]["is_alive"]
        profile_rec.is_adult = profile_data["isAdult"]
        profile_rec.avatar_link = profile_data["citizen"]["avatar"]
        profile_rec.level = profile_data["citizen"]["level"]
        profile_rec.xp = profile_data["citizenAttributes"]["experience_points"]
        profile_rec.friends_count = profile_data["friends"]["number"]
        profile_rec.achievements_count = len(profile_data["achievements"])
        profile_rec.citizenship_country = profile_data["location"]["citizenshipCountry"]["name"]
        profile_rec.residence_city = profile_data["city"]["residenceCity"]["name"]
        profile_rec.residence_region = profile_data["city"]["residenceCity"]["region_name"]
        profile_rec.residence_country = profile_data["city"]["residenceCity"]["country_name"]
        profile_rec.is_in_congress = profile_data['isCongressman']
        profile_rec.is_ambassador = profile_data['isAmbassador']
        profile_rec.is_dictator = profile_data['isDictator']
        profile_rec.is_country_president = profile_data['isPresident']
        profile_rec.is_top_player = profile_data['isTopPlayer']
        profile_rec.is_party_member = profile_data["isPartyMember"]
        profile_rec.is_party_president = profile_data["isPartyPresident"]
        profile_rec.party_name = profile_data["partyData"]["name"]
        profile_rec.party_avatar_link =\
            "https:" + profile_data["partyData"]["avatar"]
        profile_rec.party_orientation =\
            profile_data["partyData"]["economical_orientation"]
        profile_rec.party_url = self.opt.erep_url + "/party/" +\
            profile_data["partyData"]["stripped_title"] + "-" +\
            str(profile_data["partyData"]["id"]) + "/1"
        profile_rec.militia_name =\
            profile_data['military']['militaryUnit']['name']
        profile_rec.militia_url = self.opt.erep_url +\
            "/military/military-unit/" +\
            str(profile_data['military']['militaryUnit']['id']) + "/overview"
        profile_rec.militia_size =\
            profile_data['military']['militaryUnit']['member_count']
        profile_rec.militia_avatar_link =\
            "https:" + profile_data['military']['militaryUnit']["avatar"]
        profile_rec.military_rank =\
            profile_data['military']['militaryUnit']["militaryRank"]
        profile_rec.aircraft_rank =\
            profile_data['military']['militaryData']["aircraft"]["name"]
        profile_rec.ground_rank =\
            profile_data['military']['militaryData']["ground"]["name"]
        profile_rec.newspaper_name =\
            profile_data['newspaper']['name']
        profile_rec.newspaper_avatar_link =\
            "https:" + profile_data['newspaper']["avatar"]
        profile_rec.newspaper_url = self.opt.erep_url + "/main/newspaper/" +\
            profile_data['newspaper']["stripped_title"] + "-" +\
            str(profile_data['newspaper']["id"]) + "/1"

        profile_rec.hash_id = None
        profile_rec.create_ts = None
        profile_rec.update_ts = None
        profile_rec.delete_ts = None
        profile_rec.is_encrypted = None

        # Only do this when getting ready to use the pic?
        # profile_rec.avatar_file = Image.open(requests.get(profile.avatar_link,
        #                                               stream=True).raw)
        # If I do want to grab it, then it should be stored in a BLOB if in DB
        #  else probably in a filesystem rather than DB. May want to experiement
        #  with that a bit.

        if self.logme and self.opt.log_level == "DEBUG":
            self.LOG.write_log('DEBUG', "user_profile: {}".format(profile_data))
        return profile_rec

    def __set_erepublik(self):
        """
        Set request headers for eRepublik calls.

        @DEV - If not using US English, probably want to modify the Accept-Language values
        @DEV - Should User-Agent list be updated?
        @DEV - User-Agent "eMes/MO" seems odd. Not sure what that is.
        See: https://github.com/eeriks/erepublik (GitHub)
        and: https://libraries.io/pypi/eRepublik (PyPi)

        :Set:
          - {dict} request headers for login and logout connection to eRepublik
        """
        self.erep_rqst = requests.Session()
        self.erep_rqst.headers = None
        self.erep_csrf_token = None
        self.erep_rqst.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/31.0.1650.63 Chrome/31.0.1650.63 Safari/537.36'}

    def ___set_graphic_interface():
        """ Construct GUI widgets for ErepFriends app
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
            self.LOG.write_log('INFO', "Citizens ID .list saved at: {}".format(file_path))

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

    def connect(self):
        """
        Login to eRepublik
        This script accepts login credentials only from a configuration file.

        @DEV - Eventually move login credentials to an encrypted sqllite database.

        :Set: {string} CSRF token assigned after a valid login
        """
        if self.erep_csrf_token is not None:
            messagebox.showinfo(title = self.opt.m_info_title,
                                detail = self.opt.m_logged_in)
        else:
            formdata = {'citizen_email': self.opt.erep_mail_id,
                        'citizen_password': self.opt.erep_pwd,
                        "remember": '1',
                        'commit': 'Login'}
            erep_login = self.erep_rqst.post(self.opt.erep_url + "/login",
                                            data=formdata, allow_redirects=False)
            if self.logme:
                self.LOG.write_log('INFO',
                                "user login status code: {}".format(erep_login.status_code))
            if erep_login.status_code == 302:
                erep_response = self.erep_rqst.get(self.opt.erep_url)
                erep_soup = bs(erep_response.text, features="html.parser")
                soup_scripts = erep_soup.find_all("script")
                soup_script = '\n'.join(map(str, soup_scripts))
                #pylint: disable=anomalous-backslash-in-string
                regex = re.compile("csrfToken\s*:\s*\'([a-z0-9]+)\'")
                self.erep_csrf_token = regex.findall(soup_script)[0]
                self.status_text.config(text = self.opt.w_txt_connected)
                if self.logme and self.opt.log_level == 'DEBUG':
                    self.LOG.write_log('INFO', "CSRF Token:\t{}".format(self.erep_csrf_token))
                    self.LOG.write_log('INFO', "user login response:\n{}".format(soup_script))
            else:
                self.status_text.config(text = self.opt.w_txt_login_failed)

    def disconnect(self):
        """ Logout from eRepublik
        Totally guessing here.
        We get a 302 response here, which is good. But not sure if it is really terminating the user session.
        """
        formdata = {'citizen_email': self.opt.erep_mail_id,
                    'citizen_password': self.opt.erep_pwd,
                    "remember": '1',
                    'commit': 'Logout'}
        erep_logout = self.erep_rqst.post(self.opt.erep_url + "/logout",
                                           data=formdata, allow_redirects=False)
        if self.logme:
            self.LOG.write_log('INFO',
                               "user logout status code: {}".format(erep_logout.status_code))
        if erep_logout.status_code == 302:
            self.erep_csrf_token = None
            self.erep_rqst.get(self.opt.erep_url)
            self.status_text.config(text = self.opt.w_txt_disconnected)

    def exit_emsg(self):
        """ Quit the erep_friends app """
        if self.erep_csrf_token is not None:
            self.disconnect()
        self.win_ef.quit()
        self.LOG.close_logs()

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
                erep_response = requests.get(profile_url)
                # Reject list if it contains an invalid Profile ID
                if erep_response.status_code == 404:
                    messagebox.showwarning(title = self.opt.m_warn_title,
                            message = self.opt.m_bad_list,
                            detail = "\n{}".format(self.opt.m_bad_id.replace("[citizen]", profile_id)))
                    if self.logme:
                        self.LOG.write_log("WARN", "Invalid eRep Profile ID: {}".format(profile_id))
                    return False
                else:
                    # Get current name for Profile ID from eRepublik
                    citizen_profile = json.loads(erep_response.text)
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
        Construct the erep_friends app window
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

#======================
# Main
#======================
# If launched from command line...
if __name__ == "__main__":
    EM = ErepFriends()
#    EM.win_ef.mainloop()
