#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gets basic configuration, populates settings dictionary with default
values, reads `CONFIG_DIR/SETTINGS_FILE_NAME`.

Basic setup:
    calendar = get_calendar_setup(settings, password)
    preliminary_settings = read_settings()
    final_config = get_configuration(settings, cli_args)
    setup_logging(settings)

Other functions:
    get_password(settings)

"""
import configparser
import getpass
import locale
import logging
import sys
import os
import datetime
import caldav
import calview.settings
import calview.helper


def get_calendar_setup(settings: calview.settings.FrozenSettings,
                       password: str) -> caldav.Calendar:
    """Set up connection to `CALDAV_SERVER`` and specifying which
    calendar to query later on.

    This does not establish a connection yet.

    Args:
        settings: full settings
        password: password

    Returns:
        The setup Calendar we want to search later

    """
    client = caldav.DAVClient(url=settings.server,
                              username=settings.user,
                              password=password)
    my_calendar = caldav.Calendar(client=client,
                                  url=settings.cal_url)
    return my_calendar


def read_settings() -> calview.settings.ReadSettings:
    """Reads settings file.

    The setting file is : calview.settings.SETTINGS_PATH. Values
    are not validated here. Quits with error code(1), if a required
    setting is not found in the settings file.

    Notice:
        The settings file is created in calview.__init__.py.

    Returns:
        Preliminary settings(regarding only
        calview.settings.SETTINGS_PATH)

    Raises:
        SystemExit: If the settings file can't be read(indirectly via
        calview.helper.quitter)

    """
    out = calview.settings.ReadSettings.get_annotations()
    # these are not specified in calview.settings.SETTINGS_PATH
    out['config_dir'] = calview.settings.CONFIG_DIR
    out['settings_file'] = calview.settings.SETTINGS_PATH
    out['template_file'] = calview.settings.TEMPLATE_PATH
    read_config = configparser.ConfigParser()
    try:
        read_config.read(calview.settings.SETTINGS_PATH)
        # section name is the first key of SETTINGS_DEFAULTS
        section = list(calview.settings.SETTINGS_DEFAULTS.keys())[0]
        # use the annotated types of calview.settings.ReadSettings
        # dataclass to call the right method of configparser, to ensure
        # the correct types of default values (e.g. boolean)
        for setting, is_type in out.items():
            callinst = read_config
            call = callinst.get
            if isinstance(is_type, type):
                if is_type == bool:
                    call = callinst.getboolean
                if is_type == int:
                    call = callinst.getint
                value = call(section, setting)
                out[setting] = value
        return calview.settings.ReadSettings(**out)
    except configparser.Error as parse_error:
        quitmsg = ('Corrupt settings file or missing values. Try removing'
                   f'{out["config_dir"]}, this will setup the directory'
                   ' again with proper default files. Warning: This'
                   'ignores all changes made to the default files.'
                   f'Original exception: {parse_error}')
        calview.helper.quitter(None, quitmsg)


def _validate(settings: calview.settings.FrozenSettings) -> None:
    """Validates setting.

    Validation is specified by calview.validation.SETTINGS_CHECKS.
    Quitting(exit code 1) if invalid settings are found.

    Args:
        settings: full settings

    Raises:
        SystemExit: if invalid settings are found(indirectly via
        calview.helper.quitter).

    """

    invalid = list()

    for check in calview.validation.SETTINGS_CHECKS:
        call_check = check[0]
        invalid_msg = check[1]
        if call_check(settings):
            invalid_msg = invalid_msg.format(settings)
            invalid.append(invalid_msg)

    if len(invalid) > 0:
        logging.critical('Wrong configuration')
        for message in invalid:
            logging.critical(message)
        logging.critical('Exiting.')
        calview.helper.quitter(settings, 'Wrong configuration.')


def get_configuration(settings: calview.settings.ReadSettings,
                      cli_args: dict, setup_logger: bool = False,
                      validate_settings: bool = False
                      ) -> calview.settings.FrozenSettings:
    """Get final configuration.

    Manipulate settings and cli args if needed, set or generate some
    default values. Add some settings(e.g. `settings.language`) and
    assemble final configuration. Defaults to default locale(see:
    calview.settings.SETTINGS_DEFAULT) if `settings.lc_all`
    is not recognised.

    Args:
        settings: preliminary settings(as read from
        calview.settings.SETTINGS_PATH)
        cli_args: Arguments passed by CLI
        setup_logger = False: . If `True`, call `setup_logging()`.
        validate_settings = False: If `True`, call `_validate()`.

    Returns:
        Final, immutable configuration used for this run.

    """

    # setup logging first
    if cli_args['log_to_stdout']:
        settings.log_to_file = False
    if cli_args['log_file'] is not None:
        settings.log_file = cli_args['log_file'].strip()
        settings.log_to_file = True

    if cli_args['quiet']:
        settings.log_level = logging.WARNING
    if cli_args['debug']:
        settings.log_level = logging.DEBUG

    if setup_logger:
        # this allows early setup of the logger
        # but not all settings are generated yet
        # so we manually log them later on
        setup_logging(settings, settings_to_log=False)

    extra_settings = dict()
    extra_settings['local_timezone'] = datetime.datetime.now(
    ).astimezone().tzinfo
    try:
        locale.setlocale(locale.LC_ALL, settings.lc_all)
    except locale.Error as locale_error:
        logging.debug('Caught: %s', locale_error)
        logmsg = ('Wrong configuration: Locale: %s'
                  'is not valid, check: variable "lc_all" in'
                  f'{settings.settings_file}, variable: "lc_all".')
        logging.warning(logmsg, settings.lc_all)
        logmsg = 'Defaulting (lc_all) to: %s'
        default = list(calview.settings.SETTINGS_DEFAULTS.keys())[0]
        default = default['lc_all']
        logging.warning(logmsg, default)
        locale.setlocale(locale.LC_ALL, default)
    extra_settings['language'] = settings.lc_all.split('.')[0]

    if cli_args['dry_run']:
        settings.dry_run = True

    if cli_args['output_file'] is not None:
        settings.output_file = cli_args['output_file'].strip()
        settings.output_to_file = True

    dates = _get_dates(settings, cli_args['start_date'],
                       extra_settings['local_timezone'],
                       cli_args['end_date'])
    extra_settings['start_date'], extra_settings['end_date'] = dates

    full_settings = settings.get_as_frozen(**extra_settings)
    if validate_settings:
        _validate(full_settings)

    if setup_logger:
        logging.debug('settings (attribute? value): ')
        for attribute, value in vars(full_settings).items():
            logging.debug("%s? %s", attribute, value)

    return full_settings


def _get_dates(settings: calview.settings.ReadSettings, start_date: str,
               local_timezone: datetime.timezone, end_date: str = None) -> tuple:
    """Get start and end date; generate them if neccessary.

    Args:
        settings: preliminary settings(as read from
        calview.settings.SETTINGS_PATH)
        start_date: start date string(DDMMYYYY)
        local_timezone: timezone to use for start and end date
        end_date = None; end_date string(DDMMYYYY); if None, generate
        end_date

    Returns:
        Start and end date

    Raises:
        SystemExit: If start_date or end_date are malformed(indirectly
        via calview.helper.quitter)

    """
    day_span = settings.day_span
    try:
        start_date = datetime.datetime.strptime(start_date.strip(), '%d%m%Y')
        start_date = start_date.replace(tzinfo=local_timezone)
        if end_date is not None:
            end_date = datetime.datetime.strptime(end_date.strip(), '%d%m%Y')
            end_date = end_date.replace(tzinfo=local_timezone)
        else:
            end_date = start_date + datetime.timedelta(days=day_span)
    except ValueError as malformed_date:
        logging.debug('Caught: %s', malformed_date)
        logmsg = ('Wrong date format: Please use DDMMYYY. Example: '
                  '01012020. Malformed input: start_date: "%s". '
                  'Exiting (1).')
        if end_date is not None:
            logmsg = logmsg[: -14] + ' or end_date: "%s"' + logmsg[-14:]
            logging.critical(logmsg, start_date, end_date)
            calview.helper.quitter(settings, 'Malformed start / end date. ')
        else:
            logging.critical(logmsg, start_date)
            calview.helper.quitter(settings, 'Malformed start date.')
    return start_date, end_date


def setup_logging(settings: calview.settings.ReadSettings,
                  settings_to_log: bool = True) -> None:
    """Setup logging according to settings.

    Args:
        settings: preliminary settings(as read from
        calview.settings.SETTINGS_PATH)
        settings_to_log = True: If True, settings are submitted to log
        (level=debug)

    """

    logformat = ('%(asctime)s.%(msecs)03d %(levelname)s - '
                 '%(funcName)s: %(message)s')
    if settings.log_to_file:
        logging.basicConfig(filename=settings.log_file,
                            format=logformat,
                            level=settings.log_level)
    else:
        logging.basicConfig(stream=sys.stdout, format=logformat,
                            level=settings.log_level)

    logging.info('\nstarting\n')
    if settings_to_log:
        logging.debug('settings (key? value): ')
        for key, value in vars(settings).items():
            logging.debug("%s? %s", key, value)


def get_password(settings: calview.settings.FrozenSettings) -> str:
    """Get password.

    If possible, get it from the set environment variable.
    If not found, prompt user for password.

    Args:
        settings: full settings

    Returns:
        Password

    Raises:
        SystemExit: if KeyboardInterrupt is raised while prompting
        for password(indirectly via calview.helper.quitter)

    """
    env_name = settings.password_env_variable
    user = settings.user
    password = os.getenv(env_name)
    if password is None:
        hint = (f'Please set environment variable "{env_name}" if you'
                " don't want to be prompted again.")
        print(hint)
        try:
            prompt = f'User: {user}\nPassword:'
            password = getpass.getpass(prompt=prompt)
        except KeyboardInterrupt:
            logging.info('KeyboardInterrupt: Exiting (0).')
            calview.helper.quitter(settings, 'Exiting (0).', exit_code=0,
                                   print_msg_as_is=True)
    return password
