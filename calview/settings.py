#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Defines dataclasses that hold settings.

    Sets global constants; additional constants may be set in
    calview.validation and calview.connection. 
    Defines function to inititally write settings file.

    Global constants set here:
        * various default paths (see "GLOBAL CONSTANSTS")
        * SETTINGS_HELPMSG
        * CLI_DESCRIPTION
        * SETTINGS_DEFAULTS
        * CLI_OPTIONS

"""
import dataclasses
import datetime
import os
import collections
from calview.connection import CONNECTION

# GLOBAL CONSTANTS


CONFIG_DIR_NAME = '.calview'
if os.name != 'posix':
    CONFIG_DIR_NAME = 'calview'
CONFIG_DIR = os.path.expanduser('~')
CONFIG_DIR = os.path.join(CONFIG_DIR, CONFIG_DIR_NAME)
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(DATA_DIR, 'data')
TEMPLATE_FILE_NAME = 'templates.py'
SETTINGS_FILE_NAME = 'settings.ini'
SETTINGS_PATH = os.path.join(CONFIG_DIR, SETTINGS_FILE_NAME)
TEMPLATE_PATH = os.path.join(CONFIG_DIR, TEMPLATE_FILE_NAME)

# see below for SETTINGS_HELPMSG, CLI_DESCRIPTION, SETTINGS_DEFAULTS,
# CLI_OPTIONS

# Settings DATACLASSES


@dataclasses.dataclass(frozen=True)
class FrozenSettings:
    # pylint: disable=too-many-instance-attributes
    """ Holds immutable settings. All attributes are required. """
    config_dir: str
    settings_file: str
    template_file: str
    dry_run: bool
    output_file: str
    output_to_file: bool
    log_to_file: bool
    log_file: str
    log_level: int
    day_span: int
    quit_after_repeated_fails: int
    password_env_variable: str
    print_message_if_unexcepted_quit: bool
    lc_all: str
    have_seen_recurrent: str
    user: str
    server: str
    cal_url: str
    # these are generated later and not directly read
    language: str
    local_timezone: datetime.timezone
    start_date: datetime.datetime
    end_date: datetime.datetime


@dataclasses.dataclass
class ReadSettings:
    """ Holds settings as read (i. e. they may still change). Some
    needed settings are not present here, but only in FrozenSettings."""
    # pylint: disable=no-member
    # pylint: disable=too-many-instance-attributes
    config_dir: str
    settings_file: str
    template_file: str
    dry_run: bool
    output_file: str
    output_to_file: bool
    log_to_file: bool
    log_file: str
    log_level: int
    day_span: int
    quit_after_repeated_fails: int
    password_env_variable: str
    print_message_if_unexcepted_quit: bool
    lc_all: str
    have_seen_recurrent: str
    user: str
    server: str
    cal_url: str

    def get_as_frozen(self: 'ReadSettings', **additional_attributes
                      ) -> FrozenSettings:
        """Converte instance of ReadSettings to a new instance
        FrozenSettings.

        Args:
            additional_attributes: keyword/value pair(s) that corresponds
            to attributes not present in ReadSettings but present in FrozenSettings

        Returns:
            New instance of FrozenSettings with all attribute values
            of ReadSettings plus keyword expanded `additional_attributes`

        """
        return FrozenSettings(**vars(self), **additional_attributes)

    @classmethod
    def get_annotations(cls: 'ReadSettings') -> dict:
        """
        Get annotations of all attributes.

        Returns:
             A dict with attribute names as keys and types as values

        """
        return cls.__annotations__


# settings configuration

# used to write to setting file helpmsg
SETTINGS_HELPMSG = """# All values must be set.
# The following values are used as defaults.
# CLI-settings may override them.
# CLI-settings are not stored.
# Please see README for further information.\n"""


def _get_default_settings() -> dict:
    """Returns default settings.

    The keys of SETTINGS_DEFAULTS['SETTINGS'] refer to to `ReadSettings`
    attributes. More than one section (more than keyword in
    SETTINGS_DEFAULTS' first level) is not supported.

    Returns:
        Dictionary holding the default values

    """
    settings_defaults = collections.OrderedDict(
        # section name of configuration file
        SETTINGS=collections.OrderedDict(
            lc_all='de_DE.UTF-8',  # used for language
            dry_run=False,  # see calviewer -h
            output_file='output.txt',  # see calviewer -h
            output_to_file=False,  # see calviewer -h
            log_to_file=False,  # see calviewer -h
            # see calviewer -h
            log_file=str(os.path.join(CONFIG_DIR, 'output.log')),
            log_level=20,  # see calviewer -h
            # if end date is not passed as cli arg: end date = start date + day span
            day_span=14,
            # quit if so many tries have failed to mark event as seen
            quit_after_repeated_fails=2,
            # if False, error messages will only be logged
            print_message_if_unexcepted_quit=True,
            # status with which seen, recurrent events are marked
            have_seen_recurrent='TENTATIVE',  # or: CANCELLED
            user=CONNECTION['user'],
            server=CONNECTION['server'],
            password_env_variable='CALVIEW_PASS',
            cal_url=CONNECTION['cal_url']
        )
    )

    return settings_defaults


SETTINGS_DEFAULTS = _get_default_settings()

# CLI settings

# displayed, when "-h, --help" is set
# may be formatted with reference to `settings`(ReadSettings)

CLI_DESCRIPTION = ('Generate view on calendar. \n Set default values '
                   'in {settings.settings_file} change output'
                   ' formatting in {settings.template_file}')


def _get_cli_options() -> list:
    """Returns cli configuration.

    Returns:
        A list of lists, where the items of the second list are:
            * a list: passed as first argument to
            argparser.ArgParser.add_argument
            * a dictionary: passed via keyword expansion as additional
            arguments
                * if it contains key `help`, its value may be formatted
                with reference to `settings` (ReadSettings)

    """

    helpmsg = ('Format: DDMMYYYY. \n View includes events from '
               'this date until end date.')
    options = dict(help=helpmsg)
    command = ['start_date']
    start_date = [command, options]

    helpmsg = ('Format: DDMMYYYY. \n Default: End date will be '
               'calculated based on DAY_SPAN ({settings.day_span})'
               ' + START_DATE')
    command = ['-e', '--end_date']
    options = dict(required=False, help=helpmsg)
    end_date = [command, options]

    helpmsg = ('Write output to OUTPUT_FILE. Filemode: "w". Default: '
               '{settings.output_file}.')
    options = dict(required=False, help=helpmsg)
    command = ['-o', '--output_file']
    output_file = [command, options]

    helpmsg = ('Write log to LOG_FILE. Filemode: "a". Default: '
               '{settings.log_file}.')
    options = dict(required=False, help=helpmsg)
    command = ['-l', '--log_file']
    log_file = [command, options]

    helpmsg = ('Write log to STDOUT. Notice: If set, this overrides '
               '"--log-file". Default: log_to_file={settings.log_to_file}')
    options = dict(required=False, help=helpmsg, action='store_true')
    command = ['-s', '--log_to_stdout']
    log_to = [command, options]

    helpmsg = ('Set logs level to: "warning (30)". Default '
               '(higher=less logging): {settings.log_level}.')
    options = dict(required=False, help=helpmsg, action='store_true')
    command = ['-q', '--quiet']
    quiet = [command, options]

    helpmsg = ("Don't change any data in calDAV calendar. If not set, "
               'recurrent events are marked to be ignored in future runs. '
               'Default: {settings.dry_run}.')
    options = dict(required=False, help=helpmsg, action='store_true')
    command = ['-d', '--dry_run']
    dry_run = [command, options]

    helpmsg = ('Set logs level to: "debug (10)". Default '
               '(lower=more logging): {settings.log_level}.')
    options = dict(required=False, help=helpmsg, action='store_true')
    command = ['-b', '--debug']
    debug = [command, options]

    cli_options = [start_date, end_date, output_file, log_file,
                   log_to, quiet, dry_run, debug]

    return cli_options


CLI_OPTIONS = _get_cli_options()
