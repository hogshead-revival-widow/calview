#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Defines validation checks.

Checks for the following are defined:
    checking command line arguments (CLI_CHECKS)
    checking fully assembled settings (SETTINGS_CHECKS)

"""
# pylint: disable=no-member
# pylint: disable=import-error
# pylint: disable=no-name-in-module
# pylint issue #2862 (calview.templates)
import calview.templates
import calview.settings

# CLI_CHECKS


def _get_cli_checks() -> list:
    """
    Returns validation checks for checking command line arguments.

    For now, only this is checked:
        * are both cli_args['quiet'] and cli_args['debug'] set?
        * are both cli_args['output_file'] and cli_args['log_to_stdout']
        set?
        * has cli_args['start_date'] a plausible length?
        * if set, has cli_args['end_date'] a plausible length?
        * has cli_args['start_date'] only numbers in it?
        * if set, has cli_args['end_date'] only numbers in it?

    Returns:
        A lists of list, where the second list has two
        kind of items:
            * callable: function to call (full cli_args as parameter)
            * str: helpmsg (formattable with keyword expaned cli_args)

    """
    def no_quiet_and_debug(cli_args: dict) -> bool:
        ''' Returns True if both quiet and debug are set to True'''
        if cli_args['quiet'] and cli_args['debug']:
            return True
        return False

    def ambigious__log_dest(cli_args: dict) -> bool:
        ''' Returns True if log_file is set and log_to_stdout is True'''
        if cli_args['log_file'] is not None and cli_args['log_to_stdout']:
            return True
        return False

    def _helper_invalid_date_length(cli_args: dict, key: str) -> bool:
        ''' Returns True if `key` in `cli_args` has an invalid length'''
        if len(str(cli_args[key])) != 8:
            return True
        return False

    def invalid_start_date_length(cli_args: dict) -> bool:
        ''' Returns True if start_date has length != 8'''
        return _helper_invalid_date_length(cli_args, 'start_date')

    def invalid_end_date_length(cli_args: dict) -> bool:
        ''' Returns True if end_date has length != 8'''
        if cli_args['end_date'] is not None:
            return _helper_invalid_date_length(cli_args, 'end_date')
        return False

    def _helper_illegal_chars(cli_args: dict, key: str) -> bool:
        ''' Returns True if `key` in `cli_args` has illegal chars'''
        allowed_chars = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')
        has_illegal_chars = (True for char in str(cli_args[key])
                             if char not in allowed_chars)
        if any(has_illegal_chars):
            return True
        return False

    def illegalchars_start_date(cli_args: dict) -> bool:
        '''Returns True if end_date has invalid characters'''
        return _helper_illegal_chars(cli_args, 'start_date')

    def illegalchars_end_date(cli_args: dict) -> bool:
        '''Returns True if end_date has invalid characters'''
        if cli_args['end_date'] is not None:
            return _helper_illegal_chars(cli_args, 'end_date')
        return False

    # invalid messsages
    # use {key} for cli_args[key]

    no_quiet_and_debug_msg = ('You set "q-, --quiet" and "-b, '
                              '--debug".Please choose one.')
    ambigious__log_dest_msg = ('You set "-l, --log_file" and "-s, '
                               '--log_to_stdout". This is not supported.'
                               ' Please choose one.')
    invalid_start_date_length_msg = ('Wrong date format: start_date is '
                                     '"{start_date}". Please use DDMMYYY. '
                                     'Example: 01012020.')
    invalid_end_date_length_msg = ('Wrong date format: end_date is '
                                   '"{end_date}". Please use DDMMYYY. '
                                   'Example: 01012020.')
    illegalchars_start_date_msg = ('Illegal characters in "start_date". Is: '
                                   '"{start_date}". Please use characters: 0-9.'
                                   ' Example: 01012020.')
    illegalchars_end_date_msg = ('Illegal characters in "end_date". Is: '
                                 '"{end_date}". Please use characters: 0-9'
                                 '. Example: 01012020.')

    cli_checks = [
        [no_quiet_and_debug, no_quiet_and_debug_msg],
        [ambigious__log_dest, ambigious__log_dest_msg],
        [invalid_start_date_length, invalid_start_date_length_msg],
        [invalid_start_date_length, invalid_start_date_length_msg],
        [invalid_end_date_length, invalid_end_date_length_msg],
        [illegalchars_start_date, illegalchars_start_date_msg],
        [illegalchars_end_date, illegalchars_end_date_msg]
    ]
    return cli_checks


CLI_CHECKS = _get_cli_checks()

# SETTINGS_CHECKS


def _get_settings_check() -> list:
    """
    Returns validation checks for checking FrozenSettings instance.

     For now, only these are checked:
        * is `settings.settings.have_seen_recurrent` 'TENTATIVE' or
        'CANCELLED'?
        * is `settings.end_date` > settings.start_date?
        * are there templates for `settings.language`?

    Returns:
        A lists of list, where the second list has two
        kind of items:
            * callable: function to call (called w/ FrozenSettings
            instance as parameter)
            * str: invalidmsg (formattable with access to FrozenSettings
            instance)

    """
    def invalid_have_seen(settings: calview.settings.FrozenSettings) -> bool:
        ''' Returns True, if have_seen_recurrent is not TENTATIVE or CANCELLED'''
        have_seen = settings.have_seen_recurrent
        return have_seen not in ('TENTATIVE', 'CANCELLED')

    def invalid_end_date(settings: calview.settings.FrozenSettings) -> bool:
        ''' Returns True if end date is after start date. '''
        return settings.end_date < settings.start_date

    def invalid_language(settings: calview.settings.FrozenSettings) -> bool:
        ''' Returns True if there are no templates for language'''
        return settings.language not in calview.templates.templates

    invalid_have_seen_msg = ('Wrong configuration: variable'
                             ' "have_seen_recurrent" is not "TENTATIVE" or '
                             '"CANCELLED" in: {settings.settings_file}')
    invalid_end_date_msg = ('Wrong arguments: end_date'
                            ' ({settings.end_date})  is earlier than '
                            'start_date ({settings.start_date})')
    invalid_language_msg = ('Wrong configuration: Language: '
                            '"{settings.language}" is not supported, check:'
                            'variable: "lc_all" in: {settings.settings_file} .')

    settings_checks = [
        [invalid_have_seen, invalid_have_seen_msg],
        [invalid_end_date, invalid_end_date_msg],
        [invalid_language, invalid_language_msg]
    ]

    return settings_checks


SETTINGS_CHECKS = _get_settings_check()
