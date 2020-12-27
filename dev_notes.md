# Working Notes

    TODO List --

    - Explore use of the erepublik pypi library
        - Its connect, citizen.profile and possibly utils.send_mail functions look interesting

    - Include an app/db/credentials set-up method.

    - Consider alternatives to tkinter:
        - Other local GUI's: PyQt5, wxPython, Gtk
            - Qt5: Though probably worth learning, seems pretty heavy-duty to me
               Got it installed no problem. Simple hello tutorial was easy too.
               So maybe spend more time on this one.
            - wxPython: https://docs.wxpython.org/index.html looks promising, kind of low-key,
               I like the docs even tho they are kind of wonky.
               Maybe try this one? Claims to look good on Linux, Mac, Win w/o extra effort.
               Seems easy like Tk but with less bizarre terminology?
               See: https://wxpython.org/pages/overview/#hello-world to get started
               Ugh. No. Got a massive number of errors trying to install it from PyPi using Pip3.
               Looks like it relies on GTK+.
            - Python GTK+ / PyGObject: seems even heavier than Qt5. I got a headache just
               reading the install instructions. It is maybe best for creating really pro
               standalone apps using Python?
               See: https://pygobject.readthedocs.io/en/latest/
        - Game-oriented GUI's: pygame/SDL, arcade
            - See PyPi for MANY add-ons to pygame: https://pypi.org/search/?q=pygame
            - I've reviewed other game engines and think pygame is best, but might want
              to play around with arcade. Seems easy to use and they claim a number of
              improvements in a direct comparison to pygame. Examples seem sort of crappy tho'.
              See: https://arcade.academy/
        - Browser-based: Flask, Tornado + JavaScript (sure, but later)

        - I will stick with Tk and Pygame for now.

    - Consider tools interesting visualizations of analytical data:
        - pymunk: 2D Physics/movement library https://pypi.org/project/pymunk/
            This ^ seems like it could be very useful to me! :-)
            I installed 6.0.0 but arcade needs ~=5.7 so watch out for that
        - Processing in Python:
            See: https://py.processing.org/, https://py.processing.org/tutorials/, etc..
            'Install an add-on called Python Mode. You can do this by clicking on the drop-down menu on the right side of the tool bar and selecting "Add Mode..." A window with the title "Mode Manager" will appear. Scroll down until you see "Python" and press "Install."'
            - I have Python mode working, as well as JS mode. Don't have to code in Java any more!
            - There are TONS of libraries available, more than ever.
            - Might be interesting to see what could be done combining Processing with Pygame and maybe with G'MIC-Qt or ZArt?
        - plotly, matplotlib, Seaborn, GGplot, Bokeh, Altair, Pygal, Geoplotlib
            - all are good, potentially useful
            - geoplotlib seems especially interesting

    - Provide an interface for setting/storing credentials in encrypted format
        - Provide an interface for removing credentials from db too

    - Define a sqlite3 database for managing data
        - For record definitions, make good use of NamedTuples and maybe OrderedDicts
        - They can be used effectively with CSV files also
        - Provide an editor for adding/managing Discord nicks and Forum names too
        - Provide means to select / filter by ..
            - Party members
            - Militia members
            - Citizenship
        - Provide means to select / sort by ..
            - (various stuff)
        - For a given selection,  generate blocks of nn profile IDs for use in messaging
        - Database backup/restore

    - Provide for exports of data sets to csv, json, excel/ods
        - Also consider export to formatted messages (text / email)
        - Also consider export to markup (erep, bb, other)

    - Provide analytical functions
        - Consider time-series as well as snapshots

## Logging configuration

=========================================================
Set log_level to 'DEBUG' or 'INFO' in order to write to log
Log messages that match log_level or lower also display to console
Connection-responses are logged as part of DEBUG level
@DEV - Test with other standard log levels. See emsg_logger.py & emsg_constants.py
Set use_in_mem_log to 'True' to use an in-memory log file (Linux only)

## Database management

===========================

Need to add method for spinning up cron jobs if I want to do automated
  backups and purges.
For now, let's just provide a "DB management" interface so user can
  trigger backups and purges.

## eRep Session management

=========================

Consider wiping eRep-related cookies before/after connecting, disconnecting

## Encryption keys and tags

===========================

Defining a special "encryption tag" is confusing.
Just associate an encryption key with user identity.
Maybe make the app password protected.

## Minor Fixes

===========================

Logger is using local (US/Eastern) time while
  the app uses Pacific or UTC

Don't ask for optional file locations if efriends.conf already exists
Work on the GUI for handling set-up. Don't get too far down the road
  with just the console inputs.

## erepublik Class

===========================

            #  So this seems to work fine, but not entirely clear what is returned
            #  Looking thru his code, I do NOT see any function for returning the friends list
            #  It also seems to "report" a lot of activity to ?? Telegram, maybe emails?
            #  Writes to log and debug pretty often (locally) and records passwords and other keys
            #  Not so sure I like that .. have to be cautious not to push to github

            #  This is mainly about doing a lot of stuff using a script.
            #  I don't see any "logout" or "disconnect". There is a note about
            #  returning to home page after 15 minutes of inactivity.
            # player = Citizen(email=erep_email_id, password=erep_pass, auto_login=True)

    Interesting for sure, but not really what I need.

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
