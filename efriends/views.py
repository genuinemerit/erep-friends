# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Manage efriends front end.

Module:    views.py
Class:     Views/0  inherits object
Author:    PQ <pq_rfw @ pm.me>
"""
import tkinter as tk
from dataclasses import dataclass
from os import path
from pprint import pprint as pp  # noqa: F401
from tkinter import filedialog, messagebox, ttk

import requests
import webview
from PIL import Image, ImageTk

from controls import Controls
from reports import Reports
from structs import Structs
from texts import Texts
from utils import Utils

CN = Controls()
RP = Reports()
ST = Structs()
TX = Texts()
UT = Utils()


class Views(object):
    """Manage Tkinter GUI widgets for efriends app."""

    def __init__(self):
        """Initialize the Views object.

        Configure and start up the app.
        """
        self.foutypes = ["json", "csv", "html", "pdf", "df"]
        CN.check_python_version()
        CN.set_erep_headers()
        CN.configure_database()
        CN.create_log('INFO')
        CN.create_bkupdb()
        self.set_basic_interface()
        if not self.check_user():
            self.set_menu_item(TX.menu.m_win, TX.menu.i_coll, "disable")
            self.set_menu_item(TX.menu.m_win, TX.menu.i_viz, "disable")
            self.make_config_frame()

    @dataclass
    class buffer:
        """Data buffer for Views object."""

        current_frame: str = None

    # Helpers

    def set_menu_item(self,
                      p_menu: str, p_item: str,
                      p_action: str):
        """Enable or disable a menu item.

        Args:
            p_menu (str): Name of the menu
            p_item (str): Name of the menu item
            p_action (str): "enable" or "disable"
        """
        w_state = "normal" if p_action == "enable"\
            else "disabled"
        if p_menu == TX.menu.m_file:
            if p_item == TX.menu.i_close:
                # First integer refers to item's order in menu
                self.file_menu.entryconfig(0, state=w_state)
        elif p_menu == TX.menu.m_win:
            if p_item == TX.menu.i_cfg:
                self.win_menu.entryconfig(0, state=w_state)
            if p_item == TX.menu.i_coll:
                self.win_menu.entryconfig(1, state=w_state)
            if p_item == TX.menu.i_viz:
                self.win_menu.entryconfig(2, state=w_state)

    # Event handlers

    def exit_appl(self):
        """Quit the app."""
        CN.close_controls()
        self.win_root.quit()

    def close_frame(self):
        """Remove and destroy the currently-opened frame."""
        if self.buffer.current_frame == "config":
            self.cfg_frame.grid_forget()
            self.cfg_frame.destroy()
        elif self.buffer.current_frame == "collect":
            self.collect_frame.grid_forget()
            self.collect_frame.destroy()
        elif self.buffer.current_frame == "viz":
            self.viz_frame.grid_forget()
            self.viz_frame.destroy()
        self.set_menu_item(TX.menu.m_win, TX.menu.i_cfg, "enable")
        self.set_menu_item(TX.menu.m_win, TX.menu.i_coll, "enable")
        self.set_menu_item(TX.menu.m_win, TX.menu.i_viz, "enable")
        self.set_menu_item(TX.menu.m_file, TX.menu.i_close, "disable")
        setattr(self.buffer, 'current_frame', None)
        self.win_root.title(TX.title.t_app)

    def show_user_guide(self):
        """Display User Guide wiki page in browser window."""
        url = TX.urls.h_user_guide
        webview.create_window(TX.title.t_guide, url)
        webview.start()

    def show_about(self):
        """Display About wiki page in browser window."""
        url = TX.urls.h_about
        webview.create_window(TX.title.t_about, url)
        webview.start()

    def save_log_level(self):
        """Handle updates to log level."""
        log_level = str(self.log_lvl_val.get()).strip()
        ok = CN.create_log(log_level)
        if ok:
            self.show_message(ST.MsgLevel.INFO,
                              TX.msg.n_log_cfg, TX.msg.n_logging_on)

    def check_user(self) -> bool:
        """See if user record already exists.

        Returns:
            bool: True if user record exists.
        """
        usrd, _ = CN.get_user_db_record()
        if usrd is None:
            return False
        CN.enable_logging() # Default to INFO
        self.set_menu_item(TX.menu.m_win, TX.menu.i_coll, "enable")
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
            citzn_rec = CN.get_ctzn_profile_from_erep(id_info.profile_id,
                                                      True)
            CN.write_ctzn_rec(citzn_rec)
            detail = TX.msg.n_connected + "\n" + TX.msg.n_user_cfg + "\n"
            detail += TX.msg.n_greet.replace("[user]", id_info.user_name)
            self.show_message(ST.MsgLevel.INFO,
                              TX.msg.n_user_on, detail)
            self.check_user()

    def save_apikey_config(self):
        """Handle updates to user API Key."""
        erep_apikey = str(self.apikey.get()).strip()
        if erep_apikey:
            usrd, _ = CN.get_user_db_record()
            msglvl = ST.MsgLevel.INFO
            if usrd is not None:
                if CN.verify_api_key(usrd.user_erep_profile_id, erep_apikey):
                    detail = TX.msg.n_user_key_on
                    CN.write_user_rec(usrd.user_erep_profile_id,
                                      usrd.user_erep_email,
                                      usrd.user_erep_password,
                                      erep_apikey)
                else:
                    detail = TX.shit.f_user_key_fail
                    msglvl = ST.MsgLevel.ERROR
            else:
                detail = TX.shit.f_user_key_fail
                msglvl = ST.MsgLevel.ERROR
            self.show_message(msglvl, TX.msg.n_user_key_test, detail)

    def collect_friends(self):
        """Login to and logout of erep using user credentials."""
        usrd, _ = CN.get_user_db_record()
        detail = CN.get_erep_friends_data(usrd.user_erep_profile_id)
        self.show_message(ST.MsgLevel.INFO, TX.msg.n_got_friends, detail)

    def get_citizen_by_id(self):
        """Get user profile data from eRepublik."""
        msg = None
        citizen_id = str(self.citz_byid.get()).strip()
        if citizen_id:
            ctzn_d, _ = CN.get_ctzn_db_rec_by_id(citizen_id)
            if ctzn_d is not None:
                msg = TX.msg.n_citzn_on_db
                detail = TX.msg.n_updating_citzn
                is_friend = True if ctzn_d.is_user_friend == "True"\
                    else False
            else:
                msg = TX.msg.n_new_citzn
                detail = TX.msg.n_adding_citzn
                is_friend_val = self.isfriend_id_chk.get()
                is_friend = True if is_friend_val == 1 else False
            call_ok = CN.get_erep_citizen_by_id(citizen_id,
                                                False, is_friend)
            if call_ok:
                self.show_message(ST.MsgLevel.INFO, msg, detail)

    def get_citizen_by_name(self):
        """Look up Citizen profile by Name."""
        msg = None
        usrd, _ = CN.get_user_db_record()
        apikey = usrd.user_tools_api_key
        if apikey in (None, "None", ""):
            msg, detail = self.update_msg("", "",
                                          TX.msg.n_no_user_key,
                                          TX.msg.n_key_required)
        else:
            citizen_nm = str(self.citz_bynm.get()).strip()
            if citizen_nm:
                msglvl = ST.MsgLevel.INFO
                ctzn_d, _ = CN.get_citizen_db_rec_by_nm(citizen_nm)
                if ctzn_d is not None:
                    msg = TX.msg.n_citzn_on_db
                    detail = TX.msg.n_updating_citzn
                    is_friend = True if ctzn_d.is_user_friend == "True"\
                        else False
                else:
                    is_friend_val = self.isfriend_nm_chk.get()
                    is_friend = True if is_friend_val == 1 else False
                    ok, detail =\
                        CN.get_erep_citizen_by_nm(apikey, citizen_nm,
                                                False, is_friend)
                    if ok:
                        msg = TX.msg.n_new_citzn
                    else:
                        msg = TX.msg.n_problem
                        msglvl = ST.MsgLevel.WARN
                self.show_message(msglvl, msg, detail)

    def select_profile_ids_file(self):
        """Select a file containing list of profile IDs."""
        ftypes = (("All", "*.*"), ("CSV", "*.csv"), ("Text", "*.txt"))
        idfile = filedialog.askopenfilename(initialdir=UT.get_home(),
                                            title=TX.button.b_pick_file,
                                            filetypes=ftypes)
        self.idf_loc.insert(0, idfile)

    def refresh_citzns_from_file(self):
        """Collect/refresh citizen data based on a list of profile IDs.

        This will add any new IDs not yet on DB and refresh data for
        those already on the data base.
        """
        msg = None
        id_file_path = str(self.idf_loc.get()).strip()
        if id_file_path not in (None, "None", ""):
            call_ok, detail =\
                CN.refresh_citizen_data_from_file(id_file_path)
            self.show_message(ST.MsgLevel.INFO,
                              TX.msg.n_id_file_on, detail)

    def refresh_ctizns_from_db(self):
        """Refresh citizen data based on active profile IDs on DB."""
        msg = None
        msglvl = ST.MsgLevel.INFO
        ok, detail = CN.refresh_ctzn_data_from_db()
        if ok:
            msg = TX.msg.n_id_data_on
        else:
            msg = TX.msg.n_problem
            msglvl = ST.MsgLevel.WARN
        self.show_message(msglvl, msg, detail)

    def run_visualization(self):
        """Execute processes to run, display results for selected query."""
        file_types = list()
        for fty in self.foutypes:
            on_off = self.chx[fty].get()
            if on_off == 1:
                file_types.append(fty)
        msglvl = ST.MsgLevel.INFO
        if file_types:
            results = RP.run_citizen_viz(self.qry_nm, file_types)
            file_path = path.join(UT.get_home(), TX.dbs.cache_path) + "/"
            msg = TX.msg.n_files_exported
            msg = msg.replace("[cache]", file_path)
            detail = ""
            for _, val in results.items():
                detail += "{}\n".format(val.replace(file_path, ""))
        else:
            msg = TX.shit.f_no_go
            detail = TX.shit.f_no_format
            msglvl = ST.MsgLevel.ERROR
        self.show_message(msglvl, msg, detail)

    # Constructors

    def make_viz_frame(self):
        """Construct frame for reporting, visualizing citizen data."""
        def set_context():
            """Adjust menus, set frame."""
            setattr(self.buffer, 'current_frame', 'viz')
            self.win_root.title(TX.title.t_viz)
            self.set_menu_item(TX.menu.m_file, TX.menu.i_close, "enable")
            self.set_menu_item(TX.menu.m_win, TX.menu.i_cfg, "enable")
            self.set_menu_item(TX.menu.m_win, TX.menu.i_coll, "enable")
            self.set_menu_item(TX.menu.m_win, TX.menu.i_viz, "disable")
            self.viz_frame = tk.Frame(self.win_root,
                                      width=400, padx=5, pady=5)
            self.viz_frame.grid(sticky=tk.N)
            self.win_root.grid_rowconfigure(1, weight=1)
            self.win_root.grid_columnconfigure(1, weight=1)

        def set_labels():
            """Define widget labels for visualization frame."""
            set_viz_q0100_label =\
                ttk.Label(self.viz_frame,
                          text=TX.query.q_100)
            set_viz_q0100_label.grid(row=1, column=0,
                                     sticky=tk.E, padx=5)

        def set_inputs():
            """Define input widgets for visualization frame."""

            def set_file_chx(p_chx_ty: str,
                             p_row: int, p_col: int):
                """Show output options: JSON, CSV, HTML, PDF, DataFrame.

                Args:
                    p_chx_ty (str): json, csv, etc..
                    p_row (int): row of frame to display checkbox
                    p_col (int): col of frame to display checkbox
                """
                if p_chx_ty in self.foutypes:
                    chx_nm = TX.button.c_json if p_chx_ty == "json"\
                        else TX.button.c_csv if p_chx_ty == "csv"\
                        else TX.button.c_html if p_chx_ty == "html"\
                        else TX.button.c_pdf if p_chx_ty == "pdf"\
                        else TX.button.c_dataframe if p_chx_ty == "df"\
                        else None
                    if chx_nm is not None:
                        self.chx[p_chx_ty] = tk.IntVar(value=0)
                        file_chx =\
                            ttk.Checkbutton(self.viz_frame,
                                            text=chx_nm,
                                            variable=self.chx[p_chx_ty],
                                            onvalue=1, offvalue=0)
                        file_chx.grid(row=p_row, column=p_col,
                                      sticky=tk.E, padx=5)

            def set_q0100_input():
                """Collect / refresh friends data."""
                # Add output options: JSON, CSV, HTML, DataFrame
                self.qry_nm = "q0100"
                self.q0100_btn =\
                    ttk.Button(self.viz_frame,
                               text=TX.button.b_run_query,
                               command=self.run_visualization,
                               state=tk.NORMAL)
                self.q0100_btn.grid(row=1, column=1, sticky=tk.W, padx=5)
                for fky, fty in enumerate(self.foutypes):
                    set_file_chx(fty, 1, fky + 2)

            set_q0100_input()

        # make_viz_frame() MAIN:
        self.close_frame()
        self.qry_nm = None
        self.chx = dict()
        set_context()
        set_labels()
        set_inputs()

    def make_collect_frame(self):
        """Construct frame for collecting profile IDs and citizen data."""
        def set_context():
            """Adjust menus, set frame."""
            setattr(self.buffer, 'current_frame', 'collect')
            self.win_root.title(TX.title.t_coll)
            self.set_menu_item(TX.menu.m_file, TX.menu.i_close, "enable")
            self.set_menu_item(TX.menu.m_win, TX.menu.i_coll, "disable")
            self.set_menu_item(TX.menu.m_win, TX.menu.i_cfg, "enable")
            self.collect_frame = tk.Frame(self.win_root,
                                          width=400, padx=5, pady=5)
            self.collect_frame.grid(sticky=tk.N)
            self.win_root.grid_rowconfigure(1, weight=1)
            self.win_root.grid_columnconfigure(1, weight=1)

        def set_labels():
            """Define widget labels for collect frame."""
            set_friends_list_input_label =\
                ttk.Label(self.collect_frame,
                          text=TX.label.l_getfriends)
            set_friends_list_input_label.grid(row=1, column=0,
                                              sticky=tk.E, padx=5)
            get_citz_by_id_label =\
                ttk.Label(self.collect_frame,
                          text=TX.label.l_getcit_byid)
            get_citz_by_id_label.grid(row=2, column=0, sticky=tk.E, padx=5)
            get_citz_by_nm_label =\
                ttk.Label(self.collect_frame,
                          text=TX.label.l_getcit_bynm)
            get_citz_by_nm_label.grid(row=3, column=0, sticky=tk.E, padx=5)
            idf_loc_label =\
                ttk.Label(self.collect_frame,
                          text=TX.label.l_idf_loc)
            idf_loc_label.grid(row=4, column=0, sticky=tk.E, padx=5)
            db_refresh_label =\
                ttk.Label(self.collect_frame,
                          text=TX.label.l_db_refresh)
            db_refresh_label.grid(row=5, column=0, sticky=tk.E, padx=5)

        def set_inputs():
            """Define input widgets for collect frame."""

            def set_friends_list_input():
                """Collect / refresh friends data."""
                self.friends_btn =\
                    ttk.Button(self.collect_frame,
                               text=TX.button.b_getfriends,
                               command=self.collect_friends,
                               state=tk.NORMAL)
                self.friends_btn.grid(row=1, column=1, sticky=tk.W, padx=5)

            def set_ctzn_by_id_input():
                """Refresh one citizen by ID."""
                self.citz_byid = ttk.Entry(self.collect_frame, width=25)
                self.citz_byid.grid(row=2, column=1, sticky=tk.W, padx=5)
                self.isfriend_id_chk = tk.IntVar()
                isf_id_chk =\
                    ttk.Checkbutton(self.collect_frame,
                                    text=TX.button.c_is_friend,
                                    variable=self.isfriend_id_chk,
                                    onvalue=1, offvalue=0)
                isf_id_chk.grid(row=2, column=2, sticky=tk.E, padx=5)
                self.citz_by_id_btn =\
                    ttk.Button(self.collect_frame,
                               text=TX.button.b_get_ctzn_data,
                               command=self.get_citizen_by_id,
                               state=tk.NORMAL)
                self.citz_by_id_btn.grid(row=2, column=3, sticky=tk.W, padx=5)

            def set_ctzn_by_nm_input(usrd):
                """Refresh one citizen by Name.

                Args:
                    usrd (namedtuple): "data" part of user record
                """
                widget_state = tk.NORMAL\
                    if usrd.user_tools_api_key not in (None, "None", "")\
                    else tk.DISABLED
                self.citz_bynm = ttk.Entry(self.collect_frame, width=25,
                                           state=widget_state)
                self.citz_bynm.grid(row=3, column=1, sticky=tk.W, padx=5)
                self.isfriend_nm_chk = tk.IntVar()
                isf_nm_chk =\
                    ttk.Checkbutton(self.collect_frame,
                                    text=TX.button.c_is_friend,
                                    variable=self.isfriend_nm_chk,
                                    onvalue=1, offvalue=0)
                isf_nm_chk.grid(row=3, column=2, sticky=tk.E, padx=5)
                self.citz_by_nm_btn =\
                    ttk.Button(self.collect_frame,
                               text=TX.button.b_get_ctzn_data,
                               command=self.get_citizen_by_name,
                               state=widget_state)
                self.citz_by_nm_btn.grid(row=3, column=3,
                                         sticky=tk.W, padx=5)

            def set_id_by_list_input():
                """Read in a list of Profile IDs from a file."""
                self.idf_loc = ttk.Entry(self.collect_frame, width=50)
                self.idf_loc.grid(row=4, column=1, sticky=tk.W, padx=5)
                self.idf_loc_set_btn =\
                    ttk.Button(self.collect_frame,
                               text=TX.button.b_get_file,
                               command=self.select_profile_ids_file)
                self.idf_loc_set_btn.grid(row=4, column=2,
                                          sticky=tk.W, padx=5)
                self.idf_loc_get_btn =\
                    ttk.Button(self.collect_frame,
                               text=TX.button.b_get_ctzn_data,
                               command=self.refresh_citzns_from_file)
                self.idf_loc_get_btn.grid(row=4, column=3,
                                          sticky=tk.W, padx=5)

            def set_db_refresh_input():
                """Refresh all active citizen profile IDs on the database."""
                self.db_refresh_btn =\
                    ttk.Button(self.collect_frame,
                               text=TX.button.b_get_ctzn_data,
                               command=self.refresh_ctizns_from_db)
                self.db_refresh_btn.grid(row=5, column=1,
                                         sticky=tk.W, padx=5)

            set_friends_list_input()
            set_ctzn_by_id_input()
            usrd, _ = CN.get_user_db_record()
            if usrd is not None:
                set_ctzn_by_nm_input(usrd)
            set_id_by_list_input()
            set_db_refresh_input()

        # make_collect_frame() MAIN:
        self.close_frame()
        set_context()
        set_labels()
        set_inputs()

    def make_config_frame(self):
        """Construct frame for entering configuration info."""

        def prep_cfg_data():
            """Handle empty and None values."""
            # Figure out a way to store current log level
            # Maybe use a config file
            # if cfd is not None:
            #     if cfd.log_level not in (None, "None"):
            #        cf_dflt["log_lvl"] = cfd.log_level

            if usrd is not None:
                if usrd.user_erep_email not in (None, "None"):
                    usrd_dflt["email"] = usrd.user_erep_email
                if usrd.user_erep_password not in (None, "None"):
                    usrd_dflt["passw"] = usrd.user_erep_password
                if usrd.user_tools_api_key not in (None, "None"):
                    usrd_dflt["apikey"] = usrd.user_tools_api_key

        def set_context():
            """Set root and frame. Enable/disable menu items."""
            setattr(self.buffer, 'current_frame', 'config')
            self.win_root.title(TX.title.t_cfg)
            self.set_menu_item(TX.menu.m_file, TX.menu.i_close, "enable")
            self.set_menu_item(TX.menu.m_win, TX.menu.i_cfg, "disable")
            self.set_menu_item(TX.menu.m_win, TX.menu.i_coll, "enable")
            self.cfg_frame = tk.Frame(self.win_root,
                                      width=400, padx=5, pady=5)
            self.cfg_frame.grid(sticky=tk.N)
            self.win_root.grid_rowconfigure(1, weight=1)
            self.win_root.grid_columnconfigure(1, weight=1)

        def set_labels():
            """Define and assign text to data entry labels."""
            loglvl_label = ttk.Label(self.cfg_frame,
                                     text=TX.label.l_log_lvl)
            loglvl_label.grid(row=1, column=0, sticky=tk.E, padx=5)
            email_label = ttk.Label(self.cfg_frame,
                                    text=TX.label.l_email)
            email_label.grid(row=2, column=0, sticky=tk.E, padx=5)
            passlabel = ttk.Label(self.cfg_frame,
                                  text=TX.label.l_passw)
            passlabel.grid(row=3, column=0, sticky=tk.E, padx=5)
            apikey_label = ttk.Label(self.cfg_frame,
                                     text=TX.label.l_apikey)
            apikey_label.grid(row=4, column=0, sticky=tk.E, padx=5)

        def set_inputs():
            """Define and assign defaults to data input widgets."""

            def set_log_level_input():
                """Set logging level."""
                self.log_lvl_val = tk.StringVar(self.cfg_frame)
                # Store current log level in a config file
                # if cf_dflt["log_lvl"]:
                #    self.log_lvl_val.set(cf_dflt["log_lvl"])
                # else
                self.log_lvl_val.set('INFO')
                self.log_level = tk.OptionMenu(self.cfg_frame,
                                               self.log_lvl_val,
                                               *ST.LogLevel.keys())
                self.log_level.grid(row=1, column=1, sticky=tk.W, padx=5)
                self.log_save_btn =\
                    ttk.Button(self.cfg_frame,
                               text=TX.button.b_save_log_cfg,
                               command=self.save_log_level)
                self.log_save_btn.grid(row=1, column=3, sticky=tk.W, padx=5)

            def set_erep_email_input():
                """User's eRepublik login email credential."""
                self.email = ttk.Entry(self.cfg_frame, width=25)
                email_val = tk.StringVar(self.cfg_frame)
                email_val.set(usrd_dflt["email"])
                self.email.insert(0, email_val.get())
                self.email.grid(row=2, column=1, sticky=tk.W, padx=5)

            def set_erep_password_input():
                """User's eRepublik login password credential. Hidden input."""
                self.passw = ttk.Entry(self.cfg_frame, width=25, show="*")
                passw_val = tk.StringVar(self.cfg_frame)
                passw_val.set(usrd_dflt["passw"])
                self.passw.insert(0, passw_val.get())
                self.passw.grid(row=3, column=1, sticky=tk.W, padx=5)
                self.creds_save_btn =\
                    ttk.Button(self.cfg_frame,
                               text=TX.button.b_save_creds,
                               command=self.save_user_config)
                self.creds_save_btn.grid(row=3, column=3, sticky=tk.W, padx=5)

            def set_apikey_input():
                """User's eRepublik Tools API key. Hidden input."""
                self.apikey = ttk.Entry(self.cfg_frame, width=30, show="*")
                apikey_val = tk.StringVar(self.cfg_frame)
                apikey_val.set(usrd_dflt["apikey"])
                self.apikey.insert(0, apikey_val.get())
                self.apikey.grid(row=4, column=1, sticky=tk.W, padx=5)
                self.apikey_save_btn =\
                    ttk.Button(self.cfg_frame,
                               text=TX.button.b_save_apikey,
                               command=self.save_apikey_config)
                self.apikey_save_btn.grid(row=4, column=3, sticky=tk.W, padx=5)

            set_log_level_input()
            set_erep_email_input()
            set_erep_password_input()
            set_apikey_input()

        # make_config_frame() MAIN:
        self.close_frame()
        usrd_dflt = {"email": "", "passw": "", "apikey": ""}
        usrd, _ = CN.get_user_db_record()
        prep_cfg_data()
        set_context()
        set_labels()
        set_inputs()

    def show_message(self,
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
            m_title = TX.title.t_error
        elif p_msg_level == "WARN":
            m_title = TX.title.t_warn
        else:
            m_title = TX.title.t_info
        messagebox.showwarning(title=m_title, message=p_msg,
                               detail="\n{}".format(p_detail))

    def make_user_image(self):
        """Construct the avatar-display."""
        usrd, _ = CN.get_user_db_record()
        ctzd, _ = CN.get_ctzn_db_rec_by_id(usrd.user_erep_profile_id)
        user_avatar_file =\
            Image.open(requests.get(ctzd.avatar_link, stream=True).raw)
        tk_img = ImageTk.PhotoImage(user_avatar_file)
        user_avatar_img = ttk.Label(self.win_root, image=tk_img)
        user_avatar_img.image = tk_img
        user_avatar_img.place(x=750, y=450)

    def make_menus(self):
        """Construct app menus on the root window."""
        self.menu_bar = tk.Menu(self.win_root)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=TX.menu.m_file,
                                  menu=self.file_menu)
        self.file_menu.add_command(label=TX.menu.i_close,
                                   command=self.close_frame, state="disabled")
        self.file_menu.add_command(label=TX.menu.i_quit,
                                   command=self.exit_appl)

        self.win_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=TX.menu.m_win, menu=self.win_menu)
        self.win_menu.add_command(label=TX.menu.i_cfg,
                                  command=self.make_config_frame)
        self.win_menu.add_command(label=TX.menu.i_coll,
                                  command=self.make_collect_frame)
        self.win_menu.add_command(label=TX.menu.i_viz,
                                  command=self.make_viz_frame)

        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=TX.menu.m_help,
                                  menu=self.help_menu)
        self.help_menu.add_command(label=TX.menu.i_docs,
                                   command=self.show_user_guide)
        self.help_menu.add_command(label=TX.menu.i_about,
                                   command=self.show_about)

        self.win_root.config(menu=self.menu_bar)

    def set_basic_interface(self):
        """Construct GUI widgets for efriends app."""
        # Initial set of Window widgets
        self.win_root = tk.Tk()     # root app window
        self.win_root.title(TX.title.t_app)
        self.win_root.geometry('900x600+100+100')
        self.win_root.minsize(900, 600)
        self.win_root.eval('tk::PlaceWindow . center')
        # Initial set of menus
        self.make_menus()
