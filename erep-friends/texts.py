# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Text strings in American English.

For internationalization, swap this class with translated
version.

Module:  texts
Class:   Texts
Author:    PQ <pq_rfw @ pm.me>
"""
from dataclasses import dataclass
from pprint import pprint as pp  # noqa: F401


class Texts(object):
    """Static text strings."""

    @dataclass
    class title:
        """Window, frame, messagebox titles."""

        t_app: str = 'Analyze eRepublik Citizens Data'
        t_cfg: str = 'Configure ErepFriends'
        t_coll: str = 'Collect Citizen Data'
        t_info: str = "Information"
        t_warn: str = "Warning"
        t_error: str = "Error"
        t_guide: str = "User Guide"
        t_about: str = "About ErepFriends"

    @dataclass
    class menu:
        """Menus and menu items."""

        # Menus
        m_file: str = 'File'
        m_win: str = 'Windows'
        m_help: str = 'Help'
        # Menu Items
        i_save: str = 'Save'
        i_close: str = 'Close'
        i_quit: str = 'Exit'
        i_cfg: str = 'Configure ErepFriends'
        i_coll: str = 'Collect Citizen Data'
        i_docs: str = 'User Guide'
        i_about: str = 'About'

    @dataclass
    class label:
        """Input widget labels."""

        l_log_loc: str = 'Log location:'
        l_log_lvl: str = 'Log level:'
        l_bkup: str = 'Backup DBs location:'
        l_email: str = 'eRep Email Login:'
        l_passw: str = 'eRep Password:'
        l_apikey: str = 'eRep Tools API Key:'
        l_getfriends: str = 'Refresh user friends list:'
        l_getcit_byid: str = 'Get citizen data by ID:'
        l_getcit_bynm: str = 'Get citizen data by Name:'
        l_idf_loc: str = 'Get Profile IDs from file:'
        l_db_refresh: str = 'Refresh all on Database:'

    @dataclass
    class button:
        """Button and checkbox labels."""

        b_getfriends: str = 'Get and save friends data'
        b_get_ctzn_data: str = 'Get citizen data'
        b_refresh_ctzn_data: str = 'Refresh citizen data'
        b_get_file: str = 'Get File'
        b_pick_file: str = "Select a file"
        b_pick_log_path: str = "Get log file path"
        b_pick_bkup_path: str = "Get backup path"
        b_save_log_cfg: str = "Save log location and level"
        b_save_bkup_cfg: str = "Save backup location"
        b_save_creds: str = "Verify and save eRep login"
        b_save_apikey: str = "Verify and save API key"
        c_is_friend: str = "Is a friend"

    @dataclass
    class msg:
        """Message notifications."""

        n_log_cfg: str = "Log configuration saved."
        n_logging_on: str = "Loggging turned on."
        n_bkup_cfg: str = "DB backup config saved."
        n_bkup_on: str = "Backup and Archive databases enabled."
        n_user_on: str = "User verified."
        n_user_key_test: str = "Tested the API key."
        n_nf_user_key: str = "No API key."
        n_key_required: str = "Function requires a valid API key."
        n_user_cfg: str = "User credentials and profile stored."
        n_user_key_on: str = "User eRep Tools API key verified."
        n_user_key_fail: str = "User eRep Tools API key FAILED verification."
        n_connected: str = 'Login to eRepublik verified.'
        n_login_failed: str = 'eRep login failed. Please review credentials.'
        n_got_friends: str = "Friends data collected and saved."
        n_citzn_on_db: str = "Citizen already on DB."
        n_new_citzn: str = "Citizen added to DB."
        n_updating_citzn: str = "Updating citizen data on data base."
        n_adding_citzn: str = "Inserting new citizen data to data base."
        n_greet: str = 'Greetings, [user]!'
        n_problem: str = "Problem loading data."
        n_id_file_on: str = "Profile ID file processed."
        n_id_data_on: str = "Data base profile IDs processed."
        n_lookup_id: str = "Getting data for ID: "
        n_lookup_nm: str = "Getting data for name: "
        n_profiles_done: str =\
            "Number of profile IDs processed successfully: "
        n_profiles_pulled: str =\
            "Number of unique, active profile IDs from DB: "
        n_friends_pulled: str =\
            "Number of friend profile IDs retrieved: "
        n_finito: str = "*** Done ***"

    @dataclass
    class dbs:
        """File and Database names."""
        lcl_path: str = '.erep-friends'
        db_path: str = '.erep-friends/db'
        cache_path: str = '.erep-friends/cache'
        log_path: str = '.erep-friends/log'
        bkup_path: str = '.erep-friends/bkup'
        arcv_path: str = '.erep-friends/arcv'
        db_name: str = 'efriends.db'
        log_name: str = 'efriends.log'

    @dataclass
    class urls:
        """Static URLs."""
        # eRepublik and erepublik.tools
        u_erep: str = "https://www.erepublik.com/en"
        # Help pages / GitHub wiki
        h_user_guide: str =\
            "https://github.com/genuinemerit/erep-friends/wiki/User-Guide"
        h_about: str =\
            "https://github.com/genuinemerit/erep-friends/wiki/Caveat-Emptor"

    @dataclass
    class logm:
        """Log messages and labels."""

        ll_start_sess: str = "\n== Log Session started"
        ll_local_tm: str = "\n== Localhost Time: "
        ll_erep_tm: str = "\n== eRepublik Time: "
        ll_univ_tm: str = "\n== Universal Time: "
        ll_log_loc: str = "Log file location: "
        ll_log_lvl: str = "Log level :"
        ll_logout_cd: str = "Logout status code: "
        ll_login_cd: str = "Login status code: "
        ll_friends_cd: str = "Friends request status code: "
        ll_save_logout_resp: str =\
            "Logout response/redirect text saved to log dir."
        ll_save_login_resp: str = "Login response text saved to log dir."
        ll_cached_login: str = "Used cached login data for credentials."
        ll_cached_friends: str = "Used cached friends list reponse."
        ll_cached_profile: str =\
            "Citizen profile data read from cached file for ID: "
        ll_profile_file_cached: str =\
            "Citizen profile data written to cache file for ID: "

    @dataclass
    class shit:
        """Error and warning messages."""

        f_py3_req: str = "Python 3 is required."
        f_user_ver: str = "Your version is v~VERSION~."
        f_bad_path: str = "Path could not be reached: "
        f_log_lvl_req: str = "Log level must be one of: "
        f_login_failed: str =\
            "Login connection failed. See response text in log." +\
            "\n Probably a captcha. May want to wait a few hours."
        f_apikey_failed: str = "Verification of eRep Tools API key failed. "
        f_profile_id_failed: str = "Invalid eRepublik Profile ID: "
        f_upsert_failed: str = "Cannot upsert. Record not found or OID not matched."
