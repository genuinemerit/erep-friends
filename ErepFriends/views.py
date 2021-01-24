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
from PIL import Image, ImageTk
from pprint import pprint as pp                  # noqa: F401
from tkinter import filedialog, messagebox, ttk  # noqa: F401

import requests

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
            self.make_configs_editor()

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
            if p_item == self.tx.m_save:
                self.file_menu.entryconfig(0, state="normal")
            elif p_item == self.tx.m_close:
                self.file_menu.entryconfig(1, state="normal")
        elif p_menu == self.tx.m_win:
            if p_item == self.tx.m_cfg:
                self.win_menu.entryconfig(0, state="normal")

    def disable_menu_item(self, p_menu: str, p_item: str):
        """Disable a menu item.

        Args:
            p_menu (str): Name of the menu
            p_item (str): Name of the menu item
        """
        if p_menu == self.tx.m_file:
            if p_item == self.tx.m_save:
                self.file_menu.entryconfig(0, state="disabled")
            elif p_item == self.tx.m_close:
                self.file_menu.entryconfig(1, state="disabled")
        elif p_menu == self.tx.m_win:
            if p_item == self.tx.m_cfg:
                self.win_menu.entryconfig(0, state="disabled")

    def update_msg(self,
                   msg: str, detail: str,
                   mm: str, dd: str) -> tuple:
        """Format result messages.

        Args:
            mm (str): short message
            dd (str): detailed message
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
            self.connect_frame.grid_forget()
            self.connect_frame.destroy()
        self.enable_menu_item(self.tx.m_win, self.tx.m_cfg)
        self.enable_menu_item(self.tx.m_win, self.tx.m_connect)
        self.disable_menu_item(self.tx.m_file, self.tx.m_close)
        self.disable_menu_item(self.tx.m_file, self.tx.m_save)
        setattr(self.buffer, 'current_frame', None)
        self.win_root.title(self.tx.app_ttl)

    def save_log_path(self) -> tuple:
        """Handle updates to log info.

        Returns:
            tuple(str: brief_msg, str: detailed_msg)
        """
        log_path = str(self.log_loc.get()).strip()
        log_level = str(self.log_lvl_val.get()).strip()
        if CN.configure_log(log_path, log_level):
            return(self.tx.m_log_data,
                   self.tx.m_logging_on)
        else:
            return("", "")

    def save_bkup_path(self) -> tuple:
        """Handle updates to DB backup paths.

        Returns:
            tuple(str: brief_msg, str: detailed_msg)
        """
        bkup_db_path = str(self.bkup_loc.get()).strip()
        if CN.configure_backups(bkup_db_path):
            return(self.tx.m_bkup_data,
                   self.tx.m_bkups_on)
        else:
            return("", "")

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
            self.make_user_image()
            return True

    def save_user_data(self) -> tuple:
        """Handle updates to user credentials and basic info.

        Returns:
            tuple(str: brief_msg, str: detailed_msg)
        """
        erep_email = str(self.email.get()).strip()
        erep_passw = str(self.passw.get()).strip()
        erep_apikey = str(self.apikey.get()).strip()
        if erep_email and erep_passw:
            id_info = CN.verify_citizen_credentials(erep_email,
                                                    erep_passw, True)
            CN.write_user_rec(id_info.profile_id, erep_email,
                              erep_passw, erep_apikey)
            citzn_rec = CN.get_citizen_profile(id_info.profile_id, True)
            CN.write_citizen_rec(citzn_rec)
            return_detail = self.tx.connected + "\n" +\
                            self.tx.m_user_data + "\n"
            if erep_apikey:
                if CN.verify_api_key(id_info.profile_id, erep_apikey):
                    return_detail += self.tx.m_user_key_ok + "\n"
                else:
                    return_detail += self.tx.m_user_key_not_ok + "\n"
            return_detail +=\
                self.tx.greet.replace("[user]", id_info.user_name)
            return(self.tx.m_user, return_detail)
        else:
            return("", "")

    def save_data(self):
        """Write values to config file and/or database.

        For values left empty on the form or unchanged from
        existing configurations, do nothing.  Except for user
        ID and pwd. If it is entered, then always refresh.
        """
        if self.buffer.current_frame == "config":
            msg, detail = ("", "")
            rslt = list()
            rslt.append(self.save_log_path())
            rslt.append(self.save_bkup_path())
            rslt.append(self.save_user_data())
            for result in rslt:
                msg, detail = self.update_msg(msg, detail,
                                              result[0], result[1])
            self.close_frame()
            if msg is not None:
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

    def browse_file(self):
        """Browse for a selected file."""
        ftypes = (("Text files", "*.txt*"), ("all files", "*.*"))
        _ = tk.filedialog.askopenfilename(initialdir=UT.get_home(),
                                          title=self.tx.b_pick_file,
                                          filetypes=ftypes)

    def login_erep(self):
        """Login to and logout of erep using user credentials."""
        pass

    def profile_user(self):
        """Get user profile data from eRepublik."""
        pass

    # Constructors

    def make_erep_editor(self):
        """Construct frame for verifying credentials and refreshing data.

        Only do interactive connections to erep from this screen.
        Refresh user's profile.
        Refresh user's friends list.

        @DEV -- redesign as follows:
        - Option to pull in / refresh from friends list
        - Option to pull in / refresh a single profile ID
        - Option to pull in / refresh from a local list of profile IDs
        - Option to use erep tools instead of direct call to erep

        We'll make another screen for producing reports, visualzations.
        """
        def set_context():
            setattr(self.buffer, 'current_frame', 'connect')
            self.win_root.title(self.tx.connect_ttl)
            self.disable_menu_item(self.tx.m_win, self.tx.m_connect)
            self.disable_menu_item(self.tx.m_file, self.tx.m_save)
            self.enable_menu_item(self.tx.m_file, self.tx.m_close)
            self.connect_frame = tk.Frame(self.win_root,
                                          width=400, padx=5, pady=5)
            self.connect_frame.grid(sticky=tk.N)
            self.win_root.grid_rowconfigure(1, weight=1)
            self.win_root.grid_columnconfigure(1, weight=1)

        def set_labels():
            ttl_label = ttk.Label(self.connect_frame,
                                  text=self.tx.m_connect_lbl)
            ttl_label.grid(row=0, columnspan=3)
            creds_label = ttk.Label(self.connect_frame,
                                    text=self.tx.m_creds)
            creds_label.grid(row=1, column=0, sticky=tk.E)
            profile_label = ttk.Label(self.connect_frame,
                                      text=self.tx.m_profile)
            profile_label.grid(row=2, column=0, sticky=tk.E)

        def set_inputs():
            self.creds_btn = ttk.Button(self.connect_frame,
                                        text=self.tx.m_creds_btn,
                                        command=self.login_erep,
                                        state=tk.NORMAL)
            self.creds_btn.grid(row=1, column=1, sticky=tk.W)
            self.profile_btn = ttk.Button(self.connect_frame,
                                          text=self.tx.m_profile_btn,
                                          command=self.profile_user,
                                          state=tk.DISABLED)
            self.profile_btn.grid(row=2, column=1, sticky=tk.W)

        self.close_frame()
        set_context()
        set_labels()
        set_inputs()

    def make_configs_editor(self):
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
            self.disable_menu_item(self.tx.m_win, self.tx.m_cfg)
            self.disable_menu_item(self.tx.m_win, self.tx.m_connect)
            self.enable_menu_item(self.tx.m_file, self.tx.m_save)
            self.enable_menu_item(self.tx.m_file, self.tx.m_close)
            self.cfg_frame = tk.Frame(self.win_root,
                                      width=400, padx=5, pady=5)
            self.cfg_frame.grid(sticky=tk.N)
            self.win_root.grid_rowconfigure(1, weight=1)
            self.win_root.grid_columnconfigure(1, weight=1)

        def set_labels():
            """Define and assign text to data entry labels."""
            ttl_label = ttk.Label(self.cfg_frame, text=self.tx.m_cfg_lbl)
            ttl_label.grid(row=0, columnspan=3)
            log_label = ttk.Label(self.cfg_frame, text=self.tx.m_logs)
            log_label.grid(row=1, column=0, sticky=tk.E)
            loglvl_label = ttk.Label(self.cfg_frame,
                                     text=self.tx.m_log_level)
            loglvl_label.grid(row=2, column=0, sticky=tk.E)
            bkup_label = ttk.Label(self.cfg_frame, text=self.tx.m_bkups)
            bkup_label.grid(row=3, column=0, sticky=tk.E)
            email_label = ttk.Label(self.cfg_frame, text=self.tx.m_email)
            email_label.grid(row=4, column=0, sticky=tk.E)
            passlabel = ttk.Label(self.cfg_frame, text=self.tx.m_passw)
            passlabel.grid(row=5, column=0, sticky=tk.E)
            apikey_label = ttk.Label(self.cfg_frame, text=self.tx.m_apikey)
            apikey_label.grid(row=6, column=0, sticky=tk.E)

        def set_inputs():
            """Define and assign defaults to data input widgets."""

            def set_log_loc_input():
                """Log location."""
                self.log_loc = ttk.Entry(self.cfg_frame, width=50)
                log_path_val = tk.StringVar(self.cfg_frame)
                log_path_val.set(cf_dflt["log_loc"])
                self.log_loc.insert(0, log_path_val.get())
                self.log_loc.grid(row=1, column=1, sticky=tk.W)
                self.log_loc_btn = ttk.Button(self.cfg_frame,
                                            text=self.tx.m_logs_btn,
                                            command=self.select_log_dir)
                self.log_loc_btn.grid(row=1, column=2, sticky=tk.W)

            def set_log_level_input():
                """Logging level."""
                self.log_lvl_val = tk.StringVar(self.cfg_frame)
                if cf_dflt["log_lvl"]:
                    self.log_lvl_val.set(cf_dflt["log_lvl"])
                else:
                    self.log_lvl_val.set('INFO')
                self.log_level = tk.OptionMenu(self.cfg_frame,
                                            self.log_lvl_val,
                                            *self.ST.LogLevel.keys())
                self.log_level.grid(row=2, column=1, sticky=tk.W)

            def set_db_bkup_loc_input():
                """Location for DB backup and archive files."""
                self.bkup_loc = ttk.Entry(self.cfg_frame, width=50)
                bkup_path_val = tk.StringVar(self.cfg_frame)
                bkup_path_val.set(cf_dflt["bkup_path"])
                self.bkup_loc.insert(0, bkup_path_val.get())
                self.bkup_loc.grid(row=3, column=1, sticky=tk.W)
                self.bkup_loc_btn = ttk.Button(self.cfg_frame,
                                            text=self.tx.m_bkups_btn,
                                            command=self.select_bkup_dir)
                self.bkup_loc_btn.grid(row=3, column=2, sticky=tk.W)

            def set_erep_email_input():
                """User's eRepublik login email credential."""
                self.email = ttk.Entry(self.cfg_frame, width=25)
                email_val = tk.StringVar(self.cfg_frame)
                email_val.set(usr_dflt["email"])
                self.email.insert(0, email_val.get())
                self.email.grid(row=4, column=1, sticky=tk.W)

            def set_erep_password_input():
                """User's eRepublik login password credential. Hidden input."""
                self.passw = ttk.Entry(self.cfg_frame, width=25, show="*")
                passw_val = tk.StringVar(self.cfg_frame)
                passw_val.set(usr_dflt["passw"])
                self.passw.insert(0, passw_val.get())
                self.passw.grid(row=5, column=1, sticky=tk.W)

            def set_apikey_input():
                """User's eRepublik Tools API key. Hidden input."""
                self.apikey = ttk.Entry(self.cfg_frame, width=30, show="*")
                apikey_val = tk.StringVar(self.cfg_frame)
                apikey_val.set(usr_dflt["apikey"])
                self.apikey.insert(0, apikey_val.get())
                self.apikey.grid(row=6, column=1, sticky=tk.W)

            set_log_loc_input()
            set_log_level_input()
            set_db_bkup_loc_input()
            set_erep_email_input()
            set_erep_password_input()
            set_apikey_input()

        # make_configs_editor() MAIN:
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

        Handle info, warning and error.

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
        """
        Construct the status message and avatar-display
        """
        # prep data
        usrd, _ = CN.get_database_user_data()
        ctzd, _ = CN.get_citizen_data_by_id(usrd.user_erep_profile_id)
        user_avatar_file =\
            Image.open(requests.get(ctzd.avatar_link, stream=True).raw)
        tk_img = ImageTk.PhotoImage(user_avatar_file)
        user_avatar_img = ttk.Label(self.win_root, image=tk_img)
        user_avatar_img.image = tk_img
        user_avatar_img.place(x=10, y=10)

    def make_menus(self):
        """Construct the app menus on the root window."""
        self.menu_bar = tk.Menu(self.win_root)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.tx.m_file,
                                  menu=self.file_menu)
        self.file_menu.add_command(label=self.tx.m_save,
                                   command=self.save_data, state="disabled")
        self.file_menu.add_command(label=self.tx.m_close,
                                   command=self.close_frame, state="disabled")
        self.file_menu.add_command(label=self.tx.m_quit,
                                   command=self.exit_appl)

        self.win_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.tx.m_win, menu=self.win_menu)
        self.win_menu.add_command(label=self.tx.m_cfg,
                                  command=self.make_configs_editor)
        self.win_menu.add_command(label=self.tx.m_connect,
                                  command=self.make_erep_editor)

        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.tx.m_help,
                                  menu=self.help_menu)
        self.help_menu.add_command(label=self.tx.m_docs,
                                   command=self.do_nothing, state="disabled")
        self.help_menu.add_command(label=self.tx.m_about,
                                   command=self.do_nothing, state="disabled")

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
