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
