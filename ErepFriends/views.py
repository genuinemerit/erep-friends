# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Manage eRepublik friends GUI widgets.

Module:    views.py
Class:     Views/0  inherits object
Author:    PQ <pq_rfw @ pm.me>
"""
import tkinter as tk
from dataclasses import dataclass
from pprint import pprint as pp  # noqa: F401
from tkinter import messagebox, ttk

import webview
import requests
from PIL import Image, ImageTk

from controls import Controls
from utils import Utils

CN = Controls()
UT = Utils()


class Views(object):
    """GUIs for ErepFriends app."""

    def __init__(self):
        """Initialize the Views object.

        Configure and start up the app.
        """
        CN.check_python_version()
        CN.set_erep_headers()
        self.ST = CN.configure_database()
        self.tx, _ = CN.get_text_data()
        self.set_basic_interface()
        if not self.check_user():
            self.disable_menu_item(self.tx.m_win, self.tx.m_collect)
            self.make_config_frame()

    @dataclass
    class buffer:
        """Data buffer for Views object."""

        current_frame: str = None

    # Helpers
    def enable_menu_item(self, p_menu: str, p_item: str):
        """Enable a menu item.

        Args:
            p_menu (str): Name of the menu
            p_item (str): Name of the menu item
        """
        if p_menu == self.tx.m_file:
            if p_item == self.tx.m_close:
                self.file_menu.entryconfig(0, state="normal")
        elif p_menu == self.tx.m_win:
            if p_item == self.tx.m_cfg:
                self.win_menu.entryconfig(0, state="normal")
            if p_item == self.tx.m_collect:
                self.win_menu.entryconfig(1, state="normal")

    def disable_menu_item(self, p_menu: str, p_item: str):
        """Disable a menu item.

        Args:
            p_menu (str): Name of the menu
            p_item (str): Name of the menu item
        """
        if p_menu == self.tx.m_file:
            if p_item == self.tx.m_close:
                self.file_menu.entryconfig(0, state="disabled")
        elif p_menu == self.tx.m_win:
            if p_item == self.tx.m_cfg:
                self.win_menu.entryconfig(0, state="disabled")
            if p_item == self.tx.m_collect:
                self.win_menu.entryconfig(1, state="disabled")

    def update_msg(self,
                   msg: str, detail: str,
                   mm: str, dd: str) -> tuple:
        """Format result messages.

        Args:
            msg (str): previous msgs
            detail (str): previous detail
            mm (str): short message to add
            dd (str): detailed message to add
        Returns:
            tuple: (str: msg, str: detail)
        """
        if mm:
            if msg:
                msg += "\n" + mm
            else:
                msg = mm
        if dd:
            if detail:
                detail += "\n" + dd
            else:
                detail = dd
        return(msg, detail)

    # Event handlers
    def do_nothing(self):
        """Separate menu items."""   # noqa: D401
        return True

    def exit_appl(self):
        """Quit the app."""
        CN.close_controls()
        self.win_root.quit()

    def close_frame(self):
        """Remove and destroy the currently-opened frame."""
        if self.buffer.current_frame == "config":
            self.cfg_frame.grid_forget()
            self.cfg_frame.destroy()
        elif self.buffer.current_frame == "connect":
            self.collect_frame.grid_forget()
            self.collect_frame.destroy()
        self.enable_menu_item(self.tx.m_win, self.tx.m_cfg)
        self.enable_menu_item(self.tx.m_win, self.tx.m_collect)
        self.disable_menu_item(self.tx.m_file, self.tx.m_close)
        setattr(self.buffer, 'current_frame', None)
        self.win_root.title(self.tx.app_ttl)

    def show_user_guide(self):
        """Display User Guide wiki page in browser window."""
        url =\
            'https://github.com/genuinemerit/erep-friends/wiki/User-Guide'
        webview.create_window('Documentation', url)
        webview.start()

    def show_about(self):
        """Display About wiki page in browser window."""
        url =\
            'https://github.com/genuinemerit/erep-friends/wiki/Caveat-Emptor'
        webview.create_window('About', url)
        webview.start()

    def save_log_config(self):
        """Handle updates to log info."""
        log_path = str(self.log_loc.get()).strip()
        log_level = str(self.log_lvl_val.get()).strip()
        logging_on = CN.configure_log(log_path, log_level)
        if logging_on:
            msg, detail = self.update_msg("", "",
                                          self.tx.m_log_data,
                                          self.tx.m_logging_on)
            self.make_message(self.ST.MsgLevel.INFO, msg, detail)

    def save_bkup_config(self) -> tuple:
        """Handle updates to DB backup paths."""
        bkup_db_path = str(self.bkup_loc.get()).strip()
        backups_configd = CN.configure_backups(bkup_db_path)
        if backups_configd:
            msg, detail = self.update_msg("", "",
                                          self.tx.m_bkup_data,
                                          self.tx.m_bkups_on)
            self.make_message(self.ST.MsgLevel.INFO, msg, detail)

    def check_user(self) -> bool:
        """See if user record already exists.

        Returns:
            bool: True if user record exists.
        """
        usrd, _ = CN.get_database_user_data()
        if usrd is None:
            return False
        else:
            CN.enable_logging()
            self.enable_menu_item(self.tx.m_win, self.tx.m_collect)
            self.make_user_image()
            return True

    def save_user_config(self) -> tuple:
        """Handle updates to user credentials."""
        erep_email = str(self.email.get()).strip()
        erep_passw = str(self.passw.get()).strip()
        if erep_email and erep_passw:
            id_info = CN.verify_citizen_credentials(erep_email,
                                                    erep_passw, True)
            CN.write_user_rec(id_info.profile_id, erep_email, erep_passw)
            citzn_rec = CN.get_citizen_profile(id_info.profile_id, True)
            CN.write_citizen_rec(citzn_rec)
            detail = self.tx.connected + "\n" + self.tx.m_user_data + "\n"
            detail += self.tx.greet.replace("[user]", id_info.user_name)
            msg, detail = self.update_msg("", "", self.tx.m_user, detail)
            self.make_message(self.ST.MsgLevel.INFO, msg, detail)
            self.check_user()

    def save_apikey_config(self):
        """Handle updates to user API Key."""
        erep_apikey = str(self.apikey.get()).strip()
        if erep_apikey:
            usrd, _ = CN.get_database_user_data()
            if usrd is not None:
                if CN.verify_api_key(usrd.user_erep_profile_id, erep_apikey):
                    detail = self.tx.m_user_key_ok
                    CN.write_user_rec(usrd.user_erep_profile_id,
                                      usrd.user_erep_email,
                                      usrd.user_erep_password,
                                      erep_apikey)
                else:
                    detail = self.tx.m_user_key_not_ok
            else:
                detail = self.tx.m_user_key_not_ok
            msg, detail = self.update_msg("", "", self.tx.m_user_key, detail)
            self.make_message(self.ST.MsgLevel.INFO, msg, detail)

    def select_log_dir(self):
        """Browse for a log directory."""
        dirname =\
            tk.filedialog.askdirectory(initialdir=UT.get_home(),
                                       title=self.tx.b_set_log_path)
        self.log_loc.insert(0, dirname)

    def select_bkup_dir(self):
        """Browse for a backup directory."""
        dirname =\
            tk.filedialog.askdirectory(initialdir=UT.get_home(),
                                       title=self.tx.b_set_dbkup_path)
        self.bkup_loc.insert(0, dirname)

    def collect_friends(self):
        """Login to and logout of erep using user credentials."""
        usrd, _ = CN.get_database_user_data()
        CN.set_friends_list_input_data(usrd.user_erep_profile_id)

    def get_citizen_by_id(self):
        """Get user profile data from eRepublik."""
        pass

    def get_citizen_by_name(self):
        """Look up Citizen profile by Name.

        Requires use of erepublik tools API.
        """
        pass

    def select_id_file(self):
        """Browse for a file containing list of profile IDs."""
        ftypes = (("Text files", "*.txt*"), ("all files", "*.*"))
        _ = tk.filedialog.askopenfilename(initialdir=UT.get_home(),
                                          title=self.tx.b_pick_file,
                                          filetypes=ftypes)

    def read_id_file(self):
        """Collect citizen data based on a list of profile IDs."""
        pass

    # Constructors

    def make_collect_frame(self):
        """Construct frame for collecting profile IDs and citizen data."""
        def set_context():
            setattr(self.buffer, 'current_frame', 'collect')
            self.win_root.title(self.tx.collect_ttl)
            self.enable_menu_item(self.tx.m_file, self.tx.m_close)
            self.disable_menu_item(self.tx.m_win, self.tx.m_collect)
            self.enable_menu_item(self.tx.m_win, self.tx.m_cfg)
            self.collect_frame = tk.Frame(self.win_root,
                                          width=400, padx=5, pady=5)
            self.collect_frame.grid(sticky=tk.N)
            self.win_root.grid_rowconfigure(1, weight=1)
            self.win_root.grid_columnconfigure(1, weight=1)

        def set_labels():
            set_friends_list_input_label =\
                ttk.Label(self.collect_frame,
                          text=self.tx.m_getfriends)
            set_friends_list_input_label.grid(row=1, column=0,
                                              sticky=tk.E, padx=5)
            get_citz_by_id_label = ttk.Label(self.collect_frame,
                                             text=self.tx.m_getcit_byid)
            get_citz_by_id_label.grid(row=2, column=0, sticky=tk.E, padx=5)
            get_citz_by_nm_label = ttk.Label(self.collect_frame,
                                             text=self.tx.m_getcit_bynm)
            get_citz_by_nm_label.grid(row=3, column=0, sticky=tk.E, padx=5)
            idf_loc_label = ttk.Label(self.collect_frame,
                                      text=self.tx.m_idf_loc)
            idf_loc_label.grid(row=4, column=0, sticky=tk.E, padx=5)

        def set_inputs():

            def set_friends_list_input():
                """Collect / refresh friends data."""
                self.friends_btn =\
                    ttk.Button(self.collect_frame,
                               text=self.tx.m_getfriends_btn,
                               command=self.collect_friends,
                               state=tk.NORMAL)
                self.friends_btn.grid(row=1, column=1, sticky=tk.W, padx=5)

            def set_ctzn_by_id_input():
                """Refresh one citizen by ID."""
                self.citz_byid = ttk.Entry(self.collect_frame, width=25)
                # citz_byid_val = tk.StringVar(self.collect_frame)
                self.citz_byid.grid(row=2, column=1, sticky=tk.W)
                self.citz_by_id_btn =\
                    ttk.Button(self.collect_frame,
                               text=self.tx.m_getcit_byid_btn,
                               command=self.get_citizen_by_id,
                               state=tk.NORMAL)
                self.citz_by_id_btn.grid(row=2, column=2, sticky=tk.W, padx=5)

            def set_ctzn_by_nm_input():
                """Refresh one citizen by Name."""
                usrd, _ = CN.get_database_user_data()
                widget_state = tk.NORMAL\
                    if usrd.user_tools_api_key not in (None, "None", "")\
                    else tk.DISABLED
                self.citz_bynm = ttk.Entry(self.collect_frame, width=25,
                                           state=widget_state)
                # citz_bynm_val = tk.StringVar(self.collect_frame)
                self.citz_bynm.grid(row=3, column=1, sticky=tk.W)
                self.citz_by_nm_btn =\
                    ttk.Button(self.collect_frame,
                               text=self.tx.m_getcit_bynm_btn,
                               command=self.get_citizen_by_name,
                               state=widget_state)
                self.citz_by_nm_btn.grid(row=3, column=2,
                                         sticky=tk.W, padx=5)

            def set_id_by_list_input():
                """Read in a list of Profile IDs from a file."""
                self.idf_loc = ttk.Entry(self.collect_frame, width=50)
                idf_loc_val = tk.StringVar(self.collect_frame)
                idf_loc_val.set(cfd.main_db_path)
                self.idf_loc.insert(0, idf_loc_val.get())
                self.idf_loc.grid(row=4, column=1, sticky=tk.W, padx=5)
                self.idf_loc_set_btn =\
                    ttk.Button(self.collect_frame,
                               text=self.tx.m_idf_loc_set_btn,
                               command=self.select_id_file)
                self.idf_loc_set_btn.grid(row=4, column=2,
                                          sticky=tk.W, padx=5)
                self.idf_loc_get_btn =\
                    ttk.Button(self.collect_frame,
                               text=self.tx.m_idf_loc_get_btn,
                               command=self.read_id_file)
                self.idf_loc_get_btn.grid(row=4, column=3,
                                          sticky=tk.W, padx=5)

            set_friends_list_input()
            set_ctzn_by_id_input()
            set_ctzn_by_nm_input()
            set_id_by_list_input()

        # make_collect_frame() MAIN:
        self.close_frame()
        cfd, _ = CN.get_config_data()
        set_context()
        set_labels()
        set_inputs()

    def make_config_frame(self):
        """Construct frame for entering configuration info."""

        def prep_data():
            """Handle empty and None values."""
            if cfd is not None:
                if cfd.log_path not in (None, "None"):
                    cf_dflt["log_loc"] = cfd.log_path
                if cfd.log_level not in (None, "None"):
                    cf_dflt["log_lvl"] = cfd.log_level
                if cfd.bkup_db_path not in (None, "None"):
                    cf_dflt["bkup_path"] = cfd.bkup_db_path

            if usrd is not None:
                if usrd.user_erep_email not in (None, "None"):
                    usr_dflt["email"] = usrd.user_erep_email
                if usrd.user_erep_password not in (None, "None"):
                    usr_dflt["passw"] = usrd.user_erep_password
                if usrd.user_tools_api_key not in (None, "None"):
                    usr_dflt["apikey"] = usrd.user_tools_api_key

        def set_context():
            """Set root and frame. Enable/disable menu items."""
            setattr(self.buffer, 'current_frame', 'config')
            self.win_root.title(self.tx.cfg_ttl)
            self.enable_menu_item(self.tx.m_file, self.tx.m_close)
            self.disable_menu_item(self.tx.m_win, self.tx.m_cfg)
            self.enable_menu_item(self.tx.m_win, self.tx.m_collect)
            self.cfg_frame = tk.Frame(self.win_root,
                                      width=400, padx=5, pady=5)
            self.cfg_frame.grid(sticky=tk.N)
            self.win_root.grid_rowconfigure(1, weight=1)
            self.win_root.grid_columnconfigure(1, weight=1)

        def set_labels():
            """Define and assign text to data entry labels."""
            log_label = ttk.Label(self.cfg_frame, text=self.tx.m_logs)
            log_label.grid(row=1, column=0, sticky=tk.E, padx=5)
            loglvl_label = ttk.Label(self.cfg_frame,
                                     text=self.tx.m_log_level)
            loglvl_label.grid(row=2, column=0, sticky=tk.E, padx=5)
            bkup_label = ttk.Label(self.cfg_frame, text=self.tx.m_bkups)
            bkup_label.grid(row=3, column=0, sticky=tk.E, padx=5)
            email_label = ttk.Label(self.cfg_frame, text=self.tx.m_email)
            email_label.grid(row=4, column=0, sticky=tk.E, padx=5)
            passlabel = ttk.Label(self.cfg_frame, text=self.tx.m_passw)
            passlabel.grid(row=5, column=0, sticky=tk.E, padx=5)
            apikey_label = ttk.Label(self.cfg_frame, text=self.tx.m_apikey)
            apikey_label.grid(row=6, column=0, sticky=tk.E, padx=5)

        def set_inputs():
            """Define and assign defaults to data input widgets."""

            def set_log_loc_input():
                """Set log location."""
                self.log_loc = ttk.Entry(self.cfg_frame, width=50)
                log_path_val = tk.StringVar(self.cfg_frame)
                log_path_val.set(cf_dflt["log_loc"])
                self.log_loc.insert(0, log_path_val.get())
                self.log_loc.grid(row=1, column=1, sticky=tk.W, padx=5)
                self.log_loc_btn =\
                    ttk.Button(self.cfg_frame,
                               text=self.tx.b_set_log_path,
                               command=self.select_log_dir)
                self.log_loc_btn.grid(row=1, column=2, sticky=tk.W, padx=5)

            def set_log_level_input():
                """Set logging level."""
                self.log_lvl_val = tk.StringVar(self.cfg_frame)
                if cf_dflt["log_lvl"]:
                    self.log_lvl_val.set(cf_dflt["log_lvl"])
                else:
                    self.log_lvl_val.set('INFO')
                self.log_level = tk.OptionMenu(self.cfg_frame,
                                               self.log_lvl_val,
                                               *self.ST.LogLevel.keys())
                self.log_level.grid(row=2, column=1, sticky=tk.W, padx=5)
                self.log_save_btn =\
                    ttk.Button(self.cfg_frame,
                               text=self.tx.b_save_log_btn,
                               command=self.save_log_config)
                self.log_save_btn.grid(row=2, column=3, sticky=tk.W, padx=5)

            def set_db_bkup_loc_input():
                """Location for DB backup and archive files."""
                self.bkup_loc = ttk.Entry(self.cfg_frame, width=50)
                bkup_path_val = tk.StringVar(self.cfg_frame)
                bkup_path_val.set(cf_dflt["bkup_path"])
                self.bkup_loc.insert(0, bkup_path_val.get())
                self.bkup_loc.grid(row=3, column=1, sticky=tk.W, padx=5)
                self.bkup_loc_btn =\
                    ttk.Button(self.cfg_frame,
                               text=self.tx.b_set_dbkup_path,
                               command=self.select_bkup_dir)
                self.bkup_loc_btn.grid(row=3, column=2, sticky=tk.W, padx=5)
                self.bkups_save_btn =\
                    ttk.Button(self.cfg_frame,
                               text=self.tx.b_save_bkups_btn,
                               command=self.save_bkup_config)
                self.bkups_save_btn.grid(row=3, column=3, sticky=tk.W, padx=5)

            def set_erep_email_input():
                """User's eRepublik login email credential."""
                self.email = ttk.Entry(self.cfg_frame, width=25)
                email_val = tk.StringVar(self.cfg_frame)
                email_val.set(usr_dflt["email"])
                self.email.insert(0, email_val.get())
                self.email.grid(row=4, column=1, sticky=tk.W, padx=5)

            def set_erep_password_input():
                """User's eRepublik login password credential. Hidden input."""
                self.passw = ttk.Entry(self.cfg_frame, width=25, show="*")
                passw_val = tk.StringVar(self.cfg_frame)
                passw_val.set(usr_dflt["passw"])
                self.passw.insert(0, passw_val.get())
                self.passw.grid(row=5, column=1, sticky=tk.W, padx=5)
                self.creds_save_btn =\
                    ttk.Button(self.cfg_frame,
                               text=self.tx.b_save_creds_btn,
                               command=self.save_user_config)
                self.creds_save_btn.grid(row=5, column=3, sticky=tk.W, padx=5)

            def set_apikey_input():
                """User's eRepublik Tools API key. Hidden input."""
                self.apikey = ttk.Entry(self.cfg_frame, width=30, show="*")
                apikey_val = tk.StringVar(self.cfg_frame)
                apikey_val.set(usr_dflt["apikey"])
                self.apikey.insert(0, apikey_val.get())
                self.apikey.grid(row=6, column=1, sticky=tk.W, padx=5)
                self.apikey_save_btn =\
                    ttk.Button(self.cfg_frame,
                               text=self.tx.b_save_apikey_btn,
                               command=self.save_apikey_config)
                self.apikey_save_btn.grid(row=6, column=3, sticky=tk.W, padx=5)

            set_log_loc_input()
            set_log_level_input()
            set_db_bkup_loc_input()
            set_erep_email_input()
            set_erep_password_input()
            set_apikey_input()

        # make_config_frame() MAIN:
        self.close_frame()
        cf_dflt = {"log_loc": "", "log_lvl": "", "bkup_path": ""}
        usr_dflt = {"email": "", "passw": "", "apikey": ""}
        cfd, _ = CN.get_config_data()
        usrd, _ = CN.get_database_user_data()
        prep_data()
        set_context()
        set_labels()
        set_inputs()

    def make_message(self,
                     p_msg_level: str,
                     p_msg: str,
                     p_detail: str):
        """Construct and display feedback message.

        Args:
            p_msg_level (str in ST.MessageLevel.keys())
            p_msg (str) short message text
            p_detail (str) lengthier message text
        """
        if p_msg_level == "ERROR":
            m_title = self.tx.m_error_ttl
        elif p_msg_level == "WARN":
            m_title = self.tx.m_warn_ttl
        else:
            m_title = self.tx.m_info_ttl
        messagebox.showwarning(title=m_title, message=p_msg,
                               detail="\n{}".format(p_detail))

    def make_user_image(self):
        """Construct the avatar-display."""
        usrd, _ = CN.get_database_user_data()
        ctzd, _ = CN.get_citizen_data_by_id(usrd.user_erep_profile_id)
        user_avatar_file =\
            Image.open(requests.get(ctzd.avatar_link, stream=True).raw)
        tk_img = ImageTk.PhotoImage(user_avatar_file)
        user_avatar_img = ttk.Label(self.win_root, image=tk_img)
        user_avatar_img.image = tk_img
        user_avatar_img.place(x=750, y=450)

    def make_menus(self):
        """Construct the app menus on the root window."""
        self.menu_bar = tk.Menu(self.win_root)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.tx.m_file,
                                  menu=self.file_menu)
        self.file_menu.add_command(label=self.tx.m_close,
                                   command=self.close_frame, state="disabled")
        self.file_menu.add_command(label=self.tx.m_quit,
                                   command=self.exit_appl)

        self.win_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.tx.m_win, menu=self.win_menu)
        self.win_menu.add_command(label=self.tx.m_cfg,
                                  command=self.make_config_frame)
        self.win_menu.add_command(label=self.tx.m_collect,
                                  command=self.make_collect_frame)

        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.tx.m_help,
                                  menu=self.help_menu)
        self.help_menu.add_command(label=self.tx.m_docs,
                                   command=self.show_user_guide)
        self.help_menu.add_command(label=self.tx.m_about,
                                   command=self.show_about)

        self.win_root.config(menu=self.menu_bar)

    def set_basic_interface(self):
        """Construct GUI widgets for ErepFriends app.

        Add more options later. This is enough to get through configuration.
        """
        # Initial set of Window widgets
        self.win_root = tk.Tk()     # root app window
        self.win_root.title(self.tx.app_ttl)
        self.win_root.geometry('900x600+100+100')
        self.win_root.minsize(900, 600)
        self.win_root.eval('tk::PlaceWindow . center')
        # Initial set of menus
        self.make_menus()

# ======================
# Main
# ======================


if __name__ == "__main__":
    EF = Views()
    EF.win_root.mainloop()
