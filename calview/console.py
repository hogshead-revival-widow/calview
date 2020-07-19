#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Defines console script entry point.

See README for usage examples."""
import logging
import calview.configuration as cfg
import calview.cli as cli
import calview.events as events
import calview.output as out


def main() -> int:
    """Console script entry point.

    Args:
        None

    Returns:
        Exit code (0, if successful; 1 otherwise)

    Raises:
        SystemExit: If something goes wrong in one of the called
        functions or their subfunctions (indirectly via
        calview.helper.quitter)

    """
    # setup
    default_settings = cfg.read_settings()
    cli_arguments = cli.get_arguments(default_settings)
    settings = cfg.get_configuration(default_settings, cli_arguments,
                                     setup_logger=True,
                                     validate_settings=True)

    password = cfg.get_password(settings)
    waitmsg = ('Starting. \nThis may take a couple of seconds. Querying '
               'calDAV is slow.')
    if settings.print_message_if_unexcepted_quit:
        waitmsg = (f'{waitmsg} If something goes wrong, I will display '
                   'an error message.')
    print(waitmsg)
    calendar = cfg.get_calendar_setup(settings, password)

    # get events
    event_strs = events.get_events(settings, calendar)

    # generate output
    output = out.get_output(settings, event_strs)
    out.put_out(settings, output)

    logging.info('Done: Exiting (0)')

    # successfully terminated
    return 0
