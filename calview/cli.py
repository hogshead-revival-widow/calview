#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Defines and manages command line interface.

Usage:
    cli_args = get_arguments(settings)
    This returns all cli_args (validated)

"""
import argparse
import calview
import calview.helper
import calview.validation


def _get_cli_parser(settings: calview.settings.ReadSettings,
                    description: str, cli_options: list
                    ) -> argparse.ArgumentParser:
    """Setup CLI with description and arguments.

    Args:
        settings: preliminary settings (as read from
        calview.settings.SETTINGS_PATH)
        description: CLI description (displayed in "--help")
        arguments: nested list (see calview.settings.CLI_OPTIONS
        for further information regardings its structure)

    Returns:
        Set-up parser

    """
    description = description.format(settings=settings)
    parser = argparse.ArgumentParser(description=description)
    for option in cli_options:
        if 'help' in option[1].keys():
            formatted = option[1]['help'].format(settings=settings)
            option[1]['help'] = formatted
        parser.add_argument(*option[0], **option[1])
    return parser


def _validate(settings: calview.settings.ReadSettings, cli_args: dict
              ) -> None:
    """Validates cli_args.

    Validation is done as specified in calview.validation.CLI_CHECKS.
    If invalid arguments are found, print helpful  message and quit
    (error code 1).

    Args:
        settings: preliminary settings (as read from
        calview.settings.SETTINGS_PATH)
        cli_args: parsed command line arguments

    Raises:
        SystemExit: If invalid settings are found (indirectly via
        calview.helper.quitter)

    """
    quitmsgs = list()

    for check in calview.validation.CLI_CHECKS:
        call_check = check[0]
        invalid_msg = check[1]
        if call_check(cli_args):
            invalid_msg = invalid_msg.format(**cli_args)
            quitmsgs.append(invalid_msg)
    total = len(quitmsgs)
    if total > 0:
        if total == 1:
            message = f'Error: {quitmsgs[0]} \nExiting (1)'
            calview.helper.quitter(settings, message, print_always=True,
                                   print_msg_as_is=True)
        for number, message in enumerate(quitmsgs, 1):
            index = number - 1
            quitmsgs[index] = f' {number}/{total}: {message}'
        quitmsgs.insert(0, 'Errors:')
        quitmsgs.append('Exiting.')
        message = '\n'.join(quitmsgs)
        calview.helper.quitter(settings, message, print_always=True,
                               print_msg_as_is=True)


def get_arguments(settings: calview.settings.ReadSettings) -> dict:
    """Read arguments from command line.

    This is done by using the parser obtained by
    _get_cli_parser

    Args:
        settings: preliminary settings (as read from
        calview.settings.SETTINGS_PATH)

    Returns:
        Parsed command line arguments

    """
    parser = _get_cli_parser(settings, calview.settings.CLI_DESCRIPTION,
                             calview.settings.CLI_OPTIONS)
    cli_args = vars(parser.parse_args())
    _validate(settings, cli_args)
    return cli_args
