#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Defines helper functions.

Usage:
    quitter(settings, printmsg='Done!')
    starting_time = get_template(settings, 'starting_time')

"""
# pylint: disable=no-member
# pylint: disable=import-error
# pylint: disable=no-name-in-module
# pylint issue #2862 (calview.templates)
import logging
import sys
import typing
import calview.settings
import calview.templates


def quitter(settings: typing.Union[calview.settings.ReadSettings,
                                   calview.settings.FrozenSettings,
                                   None],
            printmsg: str,
            *,
            exit_code: int = 1, print_always: bool = False,
            print_msg_as_is: bool = False) -> typing.NoReturn:
    """Quit by calling sys.exit. If set to do so, write message to STDERR.

    Args:
        settings: full or preliminary settings. As there are situations
            where the quitter is called before any settings are read,
            None is an option, too.
        printmsg: message to display
        exit_code = 1: is handed over to `sys.exit(status=exit_code)`
        print_always = False;ignore
        settings.print_message_if_unexcepted_quit
        print_msg_as_is = False; if False, append error code and logfile
        destination to output; if True: print `printmsg` only

    Raises:
        SystemExit

    """

    if settings is not None:
        do_message = settings.print_message_if_unexcepted_quit
        otherwise_invisible = settings.log_to_file
        log = settings.log_file
    if settings is None:
        do_message = True
        otherwise_invisible = True
        log = "No log created yet."
    if (do_message and otherwise_invisible) or print_always:
        if not print_msg_as_is:
            printmsg = f'{printmsg} See: {log}. Exiting ({exit_code})'
        print(printmsg, file=sys.stderr)
    sys.exit(exit_code)


def get_template(settings: typing.Union[calview.settings.ReadSettings,
                                        calview.settings.FrozenSettings],
                 key: str) -> str:
    """Get the language appropriate template.

    Quits with exit code (1), if template is not found.

    Args:
        settings: full settings
        key: template name (e.g `starting_time`)

    Returns:
        Template

    Raises:
        SystemExit: If template is not found (indirectly via quitter).

    """
    language = settings.language
    templates = calview.templates.templates
    if language not in templates:
        logmsg = "Didn't find templates for language: %s. Exiting."
        logging.critical(logmsg, language)
        quitter(settings, 'Template not found.')
    my_templates = templates[language]
    if key not in my_templates:
        logmsg = "Didn't find template: %s in %s. Exiting."
        logging.critical(logmsg, key, my_templates)
        quitter(settings, 'Template not found.')
    return my_templates[key]
