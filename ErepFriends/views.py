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
from pprint import pprint as pp                  # noqa: F401
from tkinter import filedialog, messagebox, ttk  # noqa: F401

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
        self.cfgr = CN.get_config_data()
        if not self.cfgr:
            msg = "Configuration data not set up properly." +\
                  " Delete db file and restart."
            raise Exception(ValueError, msg)
        else:
            self.cfgr = self.cfgr["data"]
        self.user = CN.get_database_user_data()
        self.set_basic_interface()
        if not self.user\
            or (self.cfgr.log_path is None or
                self.cfgr.log_level is None or
                self.cfgr.bkup_db_path is None):
            self.make_configs_editor()
        # Next:
        # Integrate results of config choices into flow
        # Some simple help instructions
            # More detailed suggestions on accumulating friends
        # View log screen
        # Modify encrypt stuff so that only user table is encrypted at the
        #  column level. Do away with "encrypt_all" option. If that is desired,
        #  then use sqlite facilities to do it at the file level.
        # Verifications regarding logs, log level, backups, login credentials
        # Gather friends list and populate friends table
        # Schedule, or manually trigger backups
        # Refactor update and delete logic
        # Implement views (test out in DB;
        #   instantiate as part of table set-up)
        # Implement view-based queries
        # Implement data refreshes
        # Design, implement tools, reports, visualizations:
            # Help designing in-game PM's
            # Time-series reports on .. party members, militia members
        # Look into methods for gathering IDs without having to be friends
            # Buying (?) lists
            # Gathering lists by residence (all in a country, all in game, etc.)
        # Figure out what is going on with residenceCity
            # and any other faulty attributes

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
        if p_menu == self.cfgr.w_m_file:
            if p_item == self.cfgr.w_m_save:
                self.file_menu.entryconfig(0, state="normal")
            elif p_item == self.cfgr.w_m_close:
                self.file_menu.entryconfig(1, state="normal")
        elif p_menu == self.cfgr.w_m_win:
            if p_item == self.cfgr.w_m_cfg:
                self.win_menu.entryconfig(0, state="normal")

    def disable_menu_item(self, p_menu: str, p_item: str):
        """Disable a menu item.

        Args:
            p_menu (str): Name of the menu
            p_item (str): Name of the menu item
        """
        if p_menu == self.cfgr.w_m_file:
            if p_item == self.cfgr.w_m_save:
                self.file_menu.entryconfig(0, state="disabled")
            elif p_item == self.cfgr.w_m_close:
                self.file_menu.entryconfig(1, state="disabled")
        elif p_menu == self.cfgr.w_m_win:
            if p_item == self.cfgr.w_m_cfg:
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
        """Used for item separators in menus."""   # noqa: D401
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
        self.enable_menu_item(self.cfgr.w_m_win, self.cfgr.w_m_cfg)
        self.enable_menu_item(self.cfgr.w_m_win, self.cfgr.w_m_connect)
        self.disable_menu_item(self.cfgr.w_m_file, self.cfgr.w_m_close)
        self.disable_menu_item(self.cfgr.w_m_file, self.cfgr.w_m_save)
        setattr(self.buffer, 'current_frame', None)
        self.win_root.title(self.cfgr.w_app_ttl)

    def save_log_path(self) -> tuple:
        """Handle updates to log info.

        Returns:
            tuple(str: brief_msg, str: detailed_msg)
        """
        log_path = str(self.log_loc.get()).strip()
        log_level = str(self.log_lvl_val.get()).strip()
        if (log_path and log_path != self.cfgr.log_path) or\
           (log_level != self.cfgr.log_level):
            CN.configure_log(log_path, log_level)
            return(self.cfgr.w_m_log_data,
                   self.cfgr.w_m_logging_on)
        else:
            return("", "")

    def save_bkup_path(self) -> tuple:
        """Handle updates to DB backup paths.

        Returns:
            tuple(str: brief_msg, str: detailed_msg)
        """
        bkup_db_path = str(self.bkup_loc.get()).strip()
        if bkup_db_path != self.cfgr.bkup_db_path:
            CN.configure_backups(bkup_db_path)
            return(self.cfgr.w_m_bkup_data,
                   self.cfgr.w_m_bkups_on)
        else:
            return("", "")

    def save_user_data(self) -> tuple:
        """Handle updates to user credentials and basic info.

        Returns:
            tuple(str: brief_msg, str: detailed_msg)
        """
        erep_email = str(self.email.get()).strip()
        erep_passw = str(self.passw.get()).strip()
        if erep_email and erep_passw:
            id_info = CN.login_erep(erep_email, erep_passw, True)
            profile_data = CN.get_citizen_profile(id_info.profile_id, True)
            CN.write_user_rec(id_info.profile_id, erep_email, erep_passw)
            CN.write_friends_rec(profile_data)
            # 4. Return feedback for message to display in GUI
            # 5. Direct user to the friends window for more processing
            return(self.cfgr.w_m_user,
                   self.cfgr.w_connected + "\n" +
                   self.cfgr.w_m_user_data + "\n" +
                   self.cfgr.w_greet.replace("[user]", id_info.user_name))
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
                self.show_message(self.ST.MsgLevel.INFO, msg, detail)

    def select_log_dir(self):
        """Browse for a log directory."""
        dirname =\
            tk.filedialog.askdirectory(initialdir=UT.get_home(),
                                       title=self.cfgr.w_b_set_log_path)
        self.log_loc.insert(0, dirname)

    def select_bkup_dir(self):
        """Browse for a backup directory."""
        dirname =\
            tk.filedialog.askdirectory(initialdir=UT.get_home(),
                                       title=self.cfgr.w_b_set_dbkup_path)
        self.bkup_loc.insert(0, dirname)

    def browse_file(self):
        """Browse for a selected file."""
        ftypes = (("Text files", "*.txt*"), ("all files", "*.*"))
        _ = tk.filedialog.askopenfilename(initialdir=UT.get_home(),
                                          title=self.cfgr.w_b_pick_file,
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

        @DEV -- tweak this as follows:
        1. Provide ability to refresh user data and user profile data,
        but don't require it.
        2. This screen is mainly about gathering the friends list and
        loading the profile data for the friends list.  Should have an
        option to:
        2.a. Refresh the friends list (of profile IDs)
        2.b. Refresh the friends list profile data
        2.c. Refresh the profile data for a specific profile ID
        2.d. Pull in profile data for a list of IDs other than the friends list

        We'll make another screen for producing reports, visualzations.
        """
        def set_context():
            setattr(self.buffer, 'current_frame', 'connect')
            self.win_root.title(self.cfgr.w_connect_ttl)
            self.disable_menu_item(self.cfgr.w_m_win, self.cfgr.w_m_connect)
            self.disable_menu_item(self.cfgr.w_m_file, self.cfgr.w_m_save)
            self.enable_menu_item(self.cfgr.w_m_file, self.cfgr.w_m_close)
            self.connect_frame = tk.Frame(self.win_root,
                                          width=400, padx=5, pady=5)
            self.connect_frame.grid(sticky=tk.N)
            self.win_root.grid_rowconfigure(1, weight=1)
            self.win_root.grid_columnconfigure(1, weight=1)

        def set_labels():
            ttl_label = ttk.Label(self.connect_frame,
                                  text=self.cfgr.w_m_connect_lbl)
            ttl_label.grid(row=0, columnspan=3)
            creds_label = ttk.Label(self.connect_frame,
                                    text=self.cfgr.w_m_creds)
            creds_label.grid(row=1, column=0, sticky=tk.E)
            profile_label = ttk.Label(self.connect_frame,
                                      text=self.cfgr.w_m_profile)
            profile_label.grid(row=2, column=0, sticky=tk.E)

        def set_inputs():
            self.creds_btn = ttk.Button(self.connect_frame,
                                        text=self.cfgr.w_m_creds_btn,
                                        command=self.login_erep,
                                        state=tk.NORMAL)
            self.creds_btn.grid(row=1, column=1, sticky=tk.W)
            self.profile_btn = ttk.Button(self.connect_frame,
                                          text=self.cfgr.w_m_profile_btn,
                                          command=self.profile_user,
                                          state=tk.DISABLED)
            self.profile_btn.grid(row=2, column=1, sticky=tk.W)

        self.close_frame()
        set_context()
        set_labels()
        set_inputs()

    def make_configs_editor(self):
        """Construct frame for entering configuration info.

        @DEV: Consider adding to this:
        1. A checkbox or something to turn logging on or to make sure
           logging is always turned on (or not).
        2. Settings related to database backups.
        3. Load values into login email and passw if user record exists.
        4. Maybe some kind of integrated help or status indicators.
        5. Buttons to complement the save/close File menu options.
        """

        def set_context():
            setattr(self.buffer, 'current_frame', 'config')
            self.win_root.title(self.cfgr.w_cfg_ttl)
            self.disable_menu_item(self.cfgr.w_m_win, self.cfgr.w_m_cfg)
            self.disable_menu_item(self.cfgr.w_m_win, self.cfgr.w_m_connect)
            self.enable_menu_item(self.cfgr.w_m_file, self.cfgr.w_m_save)
            self.enable_menu_item(self.cfgr.w_m_file, self.cfgr.w_m_close)
            self.cfg_frame = tk.Frame(self.win_root,
                                      width=400, padx=5, pady=5)
            self.cfg_frame.grid(sticky=tk.N)
            self.win_root.grid_rowconfigure(1, weight=1)
            self.win_root.grid_columnconfigure(1, weight=1)

        def set_labels():
            ttl_label = ttk.Label(self.cfg_frame, text=self.cfgr.w_m_cfg_lbl)
            ttl_label.grid(row=0, columnspan=3)
            log_label = ttk.Label(self.cfg_frame, text=self.cfgr.w_m_logs)
            log_label.grid(row=1, column=0, sticky=tk.E)
            loglvl_label = ttk.Label(self.cfg_frame,
                                     text=self.cfgr.w_m_log_level)
            loglvl_label.grid(row=2, column=0, sticky=tk.E)
            bkup_label = ttk.Label(self.cfg_frame, text=self.cfgr.w_m_bkups)
            bkup_label.grid(row=3, column=0, sticky=tk.E)
            email_label = ttk.Label(self.cfg_frame, text=self.cfgr.w_m_email)
            email_label.grid(row=4, column=0, sticky=tk.E)
            passw_label = ttk.Label(self.cfg_frame, text=self.cfgr.w_m_passw)
            passw_label.grid(row=5, column=0, sticky=tk.E)

        def set_inputs():
            self.log_loc = ttk.Entry(self.cfg_frame, width=50)
            if self.cfgr.log_path:
                # Man, tikinter has some funky stuff...
                # Define a tk string, then set its value, then get its value.
                # Sheesh...
                log_path_val = tk.StringVar(self.cfg_frame)
                log_path_val.set(self.cfgr.log_path)
                self.log_loc.insert(0, log_path_val.get())
            self.log_loc.grid(row=1, column=1, sticky=tk.W)
            self.log_loc_btn = ttk.Button(self.cfg_frame,
                                          text=self.cfgr.w_m_logs_btn,
                                          command=self.select_log_dir)
            self.log_loc_btn.grid(row=1, column=2, sticky=tk.W)

            self.log_lvl_val = tk.StringVar(self.cfg_frame)
            if self.cfgr.log_level:
                self.log_lvl_val.set(self.cfgr.log_level)
            else:
                self.log_lvl_val.set('INFO')
            self.log_level = tk.OptionMenu(self.cfg_frame,
                                           self.log_lvl_val,
                                           *self.ST.LogLevel.keys())
            self.log_level.grid(row=2, column=1, sticky=tk.W)

            self.bkup_loc = ttk.Entry(self.cfg_frame, width=50)
            if self.cfgr.bkup_db_path:
                bkup_path_val = tk.StringVar(self.cfg_frame)
                bkup_path_val.set(self.cfgr.bkup_db_path)
                self.bkup_loc.insert(0, bkup_path_val.get())
            self.bkup_loc.grid(row=3, column=1, sticky=tk.W)
            self.bkup_loc_btn = ttk.Button(self.cfg_frame,
                                           text=self.cfgr.w_m_bkups_btn,
                                           command=self.select_bkup_dir)
            self.bkup_loc_btn.grid(row=3, column=2, sticky=tk.W)

            self.email = ttk.Entry(self.cfg_frame, width=25)
            self.email.grid(row=4, column=1, sticky=tk.W)
            self.passw = ttk.Entry(self.cfg_frame, width=25, show="*")
            self.passw.grid(row=5, column=1, sticky=tk.W)

        self.close_frame()
        set_context()
        set_labels()
        set_inputs()

    def show_message(self,
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
            m_title = self.cfgr.w_m_error_ttl
        elif p_msg_level == "WARN":
            m_title = self.cfgr.w_m_warn_ttl
        else:
            m_title = self.cfgr.w_m_info_ttl
        messagebox.showwarning(title=m_title, message=p_msg,
                               detail="\n{}".format(p_detail))

    def make_menus(self):
        """Construct the app menus on the root window."""
        self.menu_bar = tk.Menu(self.win_root)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.cfgr.w_m_file,
                                  menu=self.file_menu)
        self.file_menu.add_command(label=self.cfgr.w_m_save,
                                   command=self.save_data, state="disabled")
        self.file_menu.add_command(label=self.cfgr.w_m_close,
                                   command=self.close_frame, state="disabled")
        self.file_menu.add_command(label=self.cfgr.w_m_quit,
                                   command=self.exit_appl)

        self.win_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.cfgr.w_m_win, menu=self.win_menu)
        self.win_menu.add_command(label=self.cfgr.w_m_cfg,
                                  command=self.make_configs_editor)
        self.win_menu.add_command(label=self.cfgr.w_m_connect,
                                  command=self.make_erep_editor)

        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.cfgr.w_m_help,
                                  menu=self.help_menu)
        self.help_menu.add_command(label=self.cfgr.w_m_docs,
                                   command=self.do_nothing, state="disabled")
        self.help_menu.add_command(label=self.cfgr.w_m_about,
                                   command=self.do_nothing, state="disabled")

        self.win_root.config(menu=self.menu_bar)

    def set_basic_interface(self):
        """Construct GUI widgets for ErepFriends app.

        Add more options later. This is enough to get through configuration.
        """
        # Initial set of Window widgets
        self.win_root = tk.Tk()     # root app window
        self.win_root.title(self.cfgr.w_app_ttl)
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
