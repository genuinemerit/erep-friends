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
from tkinter import filedialog, messagebox, ttk

from structs import Structs
from controls import Controls

ST = Structs()
CN = Controls()


class Views(object):
    """GUIs for ErepFriends app."""

    def __init__(self):
        """Initialize the Views object.

        Configure and start up the app.
        """
        # Basic environment set-up
        CN.check_python_version()
        CN.set_erep_headers()
        CN.set_main_data_paths()
        CN.set_config_file(CN.db_dir_path, CN.cfg_file_path)
        CN.set_required_options(CN.cfg_file_path)
        # Initial GUI set-up
        self.set_basic_interface()
        # Force configuration
        try:
            _ = CN.opt.log_path
            _ = CN.opt.bkup_path
        except Exception:
            self.make_configs_editor()
        # Next:
        ## Some simple help instructions
          ## More detailed suggestions on accumulating friends
        ## Calling CN to check on status of user table
        ## Verifications regarding logs, log level, backups, login credentials
        ## Database generation and set up
        ## User table and user friends record set-up
        ## Gather friends list and populate friends table
        ## Schedule, or manually trigger backups
        ## Implement update and delete logic
        ## Implement views (test out in DB; instantiate as part of table set-up)
        ## Implement view-based queries
        ## Implement friends-data refreshes (including user-friend)
        ## Design, implement tools, reports, visualizations:
          ## Help designing in-game PM's
          ## Time-series reports on .. party members, militia members
        ## Look into methods for gathering IDs without having to be friends
        ## Figure out what is going on with residenceCity and any other faulty attributes

    @dataclass
    class buffer:
        """Data buffer for Views object."""
        current_frame: str = None

    # Event handlers
    def do_nothing(self):
        """Used for item separators in menus."""   # noqa: D401
        return True

    def exit_app(self):
        """Quit the app."""
        CN.close_controls()
        self.win_root.quit()

    def enable_menu_item(self, p_menu: str, p_item: str):
        """Enable a menu item.

        Args:
            p_menu (str): Name of the menu
            p_item (str): Name of the menu item
        """
        if p_menu == CN.opt.w_m_file:
            if p_item == CN.opt.w_m_save:
                self.file_menu.entryconfig(0, state="normal")
            elif p_item == CN.opt.w_m_close:
                self.file_menu.entryconfig(1, state="normal")
        elif p_menu == CN.opt.w_m_win:
            if p_item == CN.opt.w_m_cfg:
                self.win_menu.entryconfig(0, state="normal")

    def disable_menu_item(self, p_menu: str, p_item: str):
        """Disable a menu item.

        Args:
            p_menu (str): Name of the menu
            p_item (str): Name of the menu item
        """
        if p_menu == CN.opt.w_m_file:
            if p_item == CN.opt.w_m_save:
                self.file_menu.entryconfig(0, state="disabled")
            elif p_item == CN.opt.w_m_close:
                self.file_menu.entryconfig(1, state="disabled")
        elif p_menu == CN.opt.w_m_win:
            if p_item == CN.opt.w_m_cfg:
                self.win_menu.entryconfig(0, state="disabled")

    def close_frame(self):
        """Remove and destroy the currently-opened frame."""
        if self.buffer.current_frame == "config":
            self.cfg_frame.grid_forget()
            self.cfg_frame.destroy()
            self.enable_menu_item(CN.opt.w_m_win, CN.opt.w_m_cfg)
            self.disable_menu_item(CN.opt.w_m_file, CN.opt.w_m_close)
            self.disable_menu_item(CN.opt.w_m_file, CN.opt.w_m_save)
        setattr(self.buffer, 'current_frame', None)
        self.win_root.title(CN.opt.w_app_ttl)

    def select_log_dir(self):
        """Browse for a log directory."""
        dirname = tk.filedialog.askdirectory(initialdir = "/db",
                                             title = "Select a Log Path")
        self.log_loc.insert(0,dirname)

    def select_bkup_dir(self):
        """Browse for a backup directory."""
        dirname = tk.filedialog.askdirectory(initialdir = "/db",
                                             title = "Select a DB BackupPath")
        self.bkup_loc.insert(0,dirname)

    def browse_file(self):
        """Browse for a selected file."""
        filename = tk.filedialog.askopenfilename(initialdir = "/",
                                              title = "Select a Path",
                                            filetypes = (("Text files",
                                                            "*.txt*"),
                                                        ("all files",
                                                            "*.*")))
    # Constructors

    def make_configs_editor(self):
        """Construct frame for entering configuration info."""

        setattr(self.buffer, 'current_frame', 'config')
        self.win_root.title(CN.opt.w_cfg_ttl)
        self.disable_menu_item(CN.opt.w_m_win, CN.opt.w_m_cfg)
        self.enable_menu_item(CN.opt.w_m_file, CN.opt.w_m_save)
        self.enable_menu_item(CN.opt.w_m_file, CN.opt.w_m_close)

        self.cfg_frame = tk.Frame(self.win_root, width=400, padx=5, pady=5)
        self.cfg_frame.grid(sticky=tk.N)

        self.win_root.grid_rowconfigure(1, weight=1)
        self.win_root.grid_columnconfigure(1, weight=1)

        ttl_label = ttk.Label(self.cfg_frame, text=CN.opt.w_m_cfg_lbl)
        ttl_label.grid(row=0, columnspan=3)

        log_label = ttk.Label(self.cfg_frame, text=CN.opt.w_m_logs)
        log_label.grid(row=1, column=0, sticky=tk.E)
        bkup_label = ttk.Label(self.cfg_frame, text=CN.opt.w_m_bkups)
        bkup_label.grid(row=2, column=0, sticky=tk.E)
        email_label = ttk.Label(self.cfg_frame, text=CN.opt.w_m_email)
        email_label.grid(row=3, column=0, sticky=tk.E)
        passw_label = ttk.Label(self.cfg_frame, text=CN.opt.w_m_passw)
        passw_label.grid(row=4, column=0, sticky=tk.E)

        self.log_loc = ttk.Entry(self.cfg_frame, width=50)
        self.log_loc.grid(row=1, column=1, sticky=tk.W)
        self.log_loc_btn = ttk.Button(self.cfg_frame, text = "Select log path",
                                      command = self.select_log_dir)
        self.log_loc_btn.grid(row=1, column=2, sticky=tk.W)

        self.bkup_loc = ttk.Entry(self.cfg_frame, width=50)
        self.bkup_loc.grid(row=2, column=1, sticky=tk.W)
        self.bkup_loc_btn = ttk.Button(self.cfg_frame, text = "Select DB backup path",
                                      command = self.select_bkup_dir)
        self.bkup_loc_btn.grid(row=2, column=2, sticky=tk.W)

        self.email = ttk.Entry(self.cfg_frame, width=25)
        self.email.grid(row=3, column=1, sticky=tk.W)
        self.passw = ttk.Entry(self.cfg_frame, width=25, show="*")
        self.passw.grid(row=4, column=1, sticky=tk.W)

    def make_menus(self):
        """Construct the app menus on the root window."""
        self.menu_bar = tk.Menu(self.win_root)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=CN.opt.w_m_file, menu=self.file_menu)
        self.file_menu.add_command(label=CN.opt.w_m_save,
                                   command=self.do_nothing, state="disabled")
        self.file_menu.add_command(label=CN.opt.w_m_close,
                                   command=self.close_frame, state="disabled")
        self.file_menu.add_command(label=CN.opt.w_m_quit, command=self.exit_app)

        self.win_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=CN.opt.w_m_win, menu=self.win_menu)
        self.win_menu.add_command(label=CN.opt.w_m_cfg, command=self.make_configs_editor)

        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=CN.opt.w_m_help, menu=self.help_menu)
        self.help_menu.add_command(label=CN.opt.w_m_docs,
                                   command=self.do_nothing, state="disabled")
        self.help_menu.add_command(label=CN.opt.w_m_about,
                                   command=self.do_nothing, state="disabled")

        self.win_root.config(menu=self.menu_bar)


    def set_basic_interface(self):
        """Construct GUI widgets for ErepFriends app."""
        # Initial set of Window widgets
        self.win_root = tk.Tk()     # root app window
        self.win_root.title(CN.opt.w_app_ttl)
        self.win_root.geometry('900x600+100+100')
        self.win_root.minsize(900, 600)
        self.win_root.eval('tk::PlaceWindow . center')
        self.win_config = None      # a subsidiary window
        # Initial set of menus
        self.make_menus()

# ======================
# Main
# ======================


if __name__ == "__main__":
    EF = Views()
    EF.win_root.mainloop()
