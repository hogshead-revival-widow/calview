#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''Sets connection details as global variable
CONNECTION'''

CONNECTION = dict(
    # user name
    user='example_example',
    # the caldav URL
    # e.g. https://cloud.example.org/remote.php/dav/
    server='https://cloud.example.org/remote.php/dav/',
    # the calendar to query
    # e.g. https://cloud.example.org/remote.php/dav/calendars/user/calname/
    # if you are using nextcloud, login with the calendar owner
    # and select "copy private link" for the calendar you want
    cal_url='https://cloud.example.org/remote.php/dav/calendars/example_example/calendar/'
    # password is expected in the env variable with the name stored
    # in`settings.password_env_variable`
    # if the variable is not seth, the user is prompted for the password
)
