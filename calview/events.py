#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Defines all functions that deal with events. Defines class Event.

Usage:
    events = get_events(settings, calendar)
    next_time = get_next_occurence(settings, event)
    plausible_occurences = get_occurences(settings, starting, rrule)

"""
import datetime
import typing
import logging
import dataclasses
import collections
import dateutil
import caldav
import calview.settings
import calview.helper


@dataclasses.dataclass
class Event:
    """Holds event data.

    Its attributes correspond to the specified VEVENT attribute value.
    `Event.more`, `Event.rrule`, `Event.status may be `None`; the rest
    is required.

    Instance attributes:
        starting: corresponds to VEVENT.DTSTART
        summary: corresponds to VEVENT.SUMMARY, may be formatted using
        `starting_fullday` in calview.templates.template
        location: corresponds to VEVENT.LOCATION
        is_fullday: if the event is a fullday event
        more: corresponds to VEVENT.DESCRIPTION; None, if there is no
        description
        status: corresponds to VEVENT.STATUS; None, if there is no
        status
        rrule: corresponds to VEVENT.RRULE; None, if there is no RRULE
        (i.e., we have a single event); may be formatted, cf.
        calview.output._render_rrule

    """
    starting: typing.Union[datetime.datetime, str]
    summary: str
    location: str
    is_fullday: bool
    more: typing.Optional[str]
    status: typing.Optional[str]
    rrule: typing.Optional[str]


def get_events(settings: calview.settings.FrozenSettings,
               calendar: caldav.Calendar) -> collections.OrderedDict:
    """Get all events.

    Reads calendars events, put them in a more useful form, check
    if they are wanted and if so, include them. Lastly, sort them.
    Quits with exit code (0), if there are no (non-skipped) events.

    Args:
        settings: full settings
        calendar: configured calendar

    Returns:
        Dictionary that is ordered by date; collection of all events

    Raises:
        * SystemExit: If there is nothing to do (exit code 0), i.e.
        there are no events (indirectly via calview.helper.quitter)

    """

    events = _get_calendar_events(settings, calendar)
    event_list = list()
    failed_tries = 0
    for event in events:
        calview_event = _get_constructed_event(
            settings, event)
        caldav_event_data = dict(calendar=calendar, vevent=event,
                                 ical_data=event.data)
        if _is_skippable(settings, calview_event):
            logging.info('Skipping: %s', calview_event.summary)
            continue
        # we have a valid event!
        event_list.append(calview_event)
        logging.debug('Included as valid: %s', calview_event.summary)
        # recurent events have  a rrule
        if calview_event.rrule is not None and not settings.dry_run:
            success = _mark_event_seen(settings, calview_event,
                                       caldav_event_data,
                                       failed_tries)
            if not success:
                failed_tries += 1

    if len(event_list) < 1:
        logmsg = 'Done! There are no valid events.'
        logging.info(logmsg)
        calview.helper.quitter(settings, logmsg, exit_code=0)

    event_dict = _get_sorted_events(settings, event_list)
    return event_dict


def _get_calendar_events(settings: calview.settings.FrozenSettings,
                         calendar: caldav.Calendar) -> list:
    """Connect to calDAV and get relevant events.

    Quits with exit code (1), if connection can't be established.

    Args:
        settings: full settings
        calendar: the calendar to query

    Returns:
        List of relevant, unloaded events; needs to be interpreted for
        further use.

    Raises:
        SystemExit: If connection can't be established (indirectly via
        calview.helper.quitter)

    """
    try:
        relevant_events = calendar.date_search(start=settings.start_date,
                                               end=settings.end_date)
    except caldav.lib.error.AuthorizationError as not_authorized:
        logmsg = ('Wrong password / connection settings. Please '
                  'check section [CONNECTION], variable user, '
                  'server, calendar_url. You set them to: "%s", "%s"'
                  ' and "%s" in: "%s". Exiting (1)')
        logging.critical(logmsg, settings.user, settings.server,
                         settings.calendar_url, settings.settings_file)
        logging.debug('Caught: %s', not_authorized)
        quitmsg = 'Connection failed: Wrong password?'
        calview.helper.quitter(settings, quitmsg)
    except caldav.lib.error.NotFoundError as not_found:
        logmsg = ('Calendar / Server not found. Does it exist? Please '
                  'check section [CONNECTION], variable calendar_url '
                  'and variable server. You set them to: "%s" and "%s"'
                  ' in: "%s". Exiting (1)')
        logging.critical(logmsg, settings.calendar_url, settings.server,
                         settings.settings_file)
        logging.debug('Caught: %s', not_found)
        calview.helper.quitter(settings, 'Calendar / Server not found.')

    return relevant_events


def _mark_event_seen(settings: calview.settings.FrozenSettings,
                     event: Event, caldav_event_data: dict,
                     failed_tries: int) -> bool:
    """Mark event as as seen by changing its VEVENT.STATUS to settings.
    have_seen_recurrent.

    Call this instead of __wrapped_mark_recurrent_event(). This
    wraps that function and tries to rollback changes if marking goes
    wrong. In that case, it quits with exit code (1), if the number of
    repeated fails exceed calview.settings.quit_after_repeated_fails.

    Args:
        settings: full settings
        event: the event to mark
        caldav_event_data: dict holding what's neccesary for manipulation
        of online caldav event. (see: _get_constructed_event for its
        structure)
        failed_tries: previously failed tries

    Returns:
        True: if no error occured. Otherwise: False.

    Raises:
        SystemExit: If number of repeated fails exceed
        settings.quit_after_repeated_fails (indirectly via
        calview.helper.quitter)

    """
    dry_run = settings.dry_run
    have_seen = settings.have_seen_recurrent
    caldav_event = caldav_event_data['vevent']
    if not dry_run:
        # if this goes wrong, there may be some non-wanted changes
        # in the online calendar, so we want to reset changes
        try:
            __wrapped_mark_recurrent_event(event, caldav_event, have_seen)
        # we want to catch it this generally
        # so that we can ensure a rollback is tried in every
        # case that may have changed data
        # pylint: disable=broad-except
        except Exception as any_exception:
            logmsg = ('Failed: Marking as recurrent: %s. Data'
                      ' may have changed. Original exception: %s')
            logging.warning(logmsg, event.summary, any_exception)
            _reset_event(event, caldav_event_data)
            quit_after = settings.quit_after_repeated_fails
            if failed_tries >= quit_after:
                logmsg = ('Maximum number (%s/%s) of failed tries'
                          'exceeded. Exiting (1).')
                logging.critical(logmsg, failed_tries, quit_after)
                quitmsg = 'Marking events as recurrent failed.'
                calview.helper.quitter(settings, quitmsg)
            else:
                return False
    else:
        logmsg = ('Dry run: Not changing any data. Event: "%s"'
                  ' is NOT being  marked as seen (vevent.status)'
                  ' not changed to "%s" and thus NOT ignored in '
                  ' future.')
        logging.warning(logmsg, event.summary, have_seen)
    return True


def __wrapped_mark_recurrent_event(event: Event,
                                   caldav_event: caldav.Event,
                                   have_seen: str) -> None:
    """Changes VEVENT.STATUS(on the server) to `have_seen`.

    If VEVENT.STATUS doesn't exist, it is added. Its better to call
    _mark_event_seen as that wraps this function (i.e. handling
    possible errors).

    Args:
        caldav_event: the event we need to manipulate
        event: interpreted representation of this VEVENT
        dry_run: If True, nothing is marked
        have_seen: "CANCELLED" or "TENTATIVE"

    """
    if not hasattr(caldav_event.instance.vevent, "status"):
        caldav_event.instance.vevent.add('status')
        logging.debug('Adding: STATUS to VEVENT')
    caldav_event.instance.vevent.status.value = have_seen
    caldav_event.save()
    logmsg = ('Changing: "%s" vevent.status to: "%s".'
              'Will be ignored in future')
    logging.info(logmsg, event.summary, have_seen)


def _reset_event(event: Event, caldav_event_data: dict) -> None:
    """Delete `event` in online calendar and create a new event with the
    original data of `event`.

    Args:
        event: the event to reset
        caldav_event_data: dict holding what's neccesary for manipulation
        of online caldav event. (see: _get_constructed_event() for structure)

    """
    calendar = caldav_event_data['calendar']
    caldav_event = caldav_event_data['vevent']
    ical_data = caldav_event_data['ical_data']
    logging.info('Rolling back: %s', event.summary)
    logging.debug('Using following data for rollback')
    logging.debug(ical_data)
    try:
        caldav_event.delete()
        calendar.add_event(ical_data)
    # for now, we want to catch all exceptions here
    # pylint: disable=broad-except
    except Exception as any_exception:
        logging.warning('Rollback may have failed, for: %s',
                        event.summary)
        logging.warning('Caught: %s', any_exception)


def _get_constructed_event(settings: calview.settings.FrozenSettings,
                           event: caldav.Event) -> Event:
    """ Create instance of Event.

    This populates the new instance with values of caldav.Event and
    calculate next occurence (via: get_next_occurence)

    Args:
        settings: full settings
        event: not yet loaded caldav.Event as in the list returned by
        calview.online:_get_calendar_events

    Returns:
        Populated instance of Event

    """
    event.load()
    starting = _get_value(event, 'dtstart')
    summary = _get_value(event, 'summary')
    if summary is not None:
        summary = summary.strip("\n")
    logging.debug('Assembling: %s', summary)
    location = _get_value(event, 'location')
    if location is not None:
        location = location.strip("\n")
    more = _get_value(event, 'description')
    status = _get_value(event, 'status')
    # if it is a fullday event, the used caldav library
    # returns it as a `date` object, but we want a uniform
    # `starting` attribute to ease handling
    is_fullday = False
    if not isinstance(starting, datetime.datetime):
        local_timezone = settings.local_timezone
        mintime = datetime.datetime.min.time()
        starting = datetime.datetime.combine(starting, mintime,
                                             tzinfo=local_timezone)
        is_fullday = True
    rrule = _get_value(event, 'rrule')
    if rrule is not None:
        starting = get_next_occurence(settings,
                                      starting, rrule)
    # put event together
    return Event(starting, summary, location,
                 is_fullday, more, status, rrule)


def _get_value(event: caldav.Event,
               attribute_name: str) -> typing.Union[str,
                                                    datetime.datetime,
                                                    datetime.date]:
    """Helper function to simplify access to nested
    Caldav.instance.vevent.{attribute_name}.value

    Args:
        event: event whose value is wanted
        attribute_name: the nested attribute, whose value is wanted

    Returns:
        Usually the value as string, however if `attribute_name` is
        'dtstart' a datetime or date object is returned. None is
        returned, if the attribute is not there / has no value.

    """

    event = event.instance.vevent
    out = getattr(event, attribute_name, None)
    if out is not None:
        out = getattr(out, 'value', None)
        if attribute_name == 'dtstart':
            return out
        out = str(out).strip()
    return out


def _get_sorted_events(settings: calview.settings.FrozenSettings,
                       events: typing.List[Event]
                       ) -> collections.OrderedDict:
    """Sort events based on their start time.

    Sorts `List[Event]` based on the events start time (Event.starting).

    Args:
        settings: full settings
        event_list: lists of events

    Returns:
        Sorted events. The dicts keys are formatted according to template
        `day_header`. Its values are of type List[Event]; i.e. all
        events that start on the same day are collected under the same
        key.

    """
    out = collections.OrderedDict()
    events.sort(key=lambda x: x.starting)
    day_header = calview.helper.get_template(settings, "day_header")
    # generate event header (e.g. [Mo, 23.01])
    for item in events:
        key = item.starting.strftime(day_header)
        out[key] = out.get(key, list())
        out[key].append(item)
    return out


def get_occurences(settings: calview.settings.FrozenSettings,
                   starting: datetime.datetime,
                   rrule: str, include_after_end_date: bool = False
                   ) -> typing.Optional[list]:
    """Generate all occurences based on rrule (within settings.start_date
    and settings.end_date).

    If UNTIL or COUNT is set, they are regarded. If both are not set,
    the maximum of generated occurences is set to 20.

    Args:
        settings: full settings
        starting: event start time
        rrule: raw rrule (as in vevent.rrule)
        include_after_end_date = False: If True, generate occurences
        after settings.end_date

    Returns:
        List of occurences; if there are none, None is returned.

    """
    start_date = settings.start_date
    end_date = settings.end_date
    if 'UNTIL' in rrule:
        # we treat, a bit hacky,
        # rrule always as timezone-aware as per RFC (2445 p.42)
        elements = rrule.split(';')
        for index, element in enumerate(elements):
            if element.startswith('UNTIL') and not element.endswith('Z'):
                elements[index] = element + 'Z'
                break
        rrule = ';'.join(elements)
    if 'UNTIL' not in rrule and 'COUNT' not in rrule:
        # limit the numbers of generated occurences
        rrule = rrule + ";COUNT=20"
    rrule = dateutil.rrule.rrulestr(rrule, dtstart=starting)

    # pylint: disable=multiple-statements
    # this is more readable than lambda
    def include(occurence): return start_date <= occurence <= end_date
    if include_after_end_date:
        # pylint: disable=function-redefined
        def include(occurence): return start_date <= occurence

    occurences = [occurence for occurence in list(rrule)
                  if include(occurence)]
    if len(occurences) == 0:
        return None
    return occurences


def get_next_occurence(settings: calview.settings.FrozenSettings,
                       starting: datetime.datetime,
                       rrule: str) -> typing.Optional[datetime.datetime]:
    """Generate the next occurent of event based on its rrule.

    Args:
        settings: full settings
        rrule: recurrence rule (vevent.rrule)

    Returns:
        If found, next occurence is returned; otherwise None.

    """
    occurences = get_occurences(settings, starting, rrule)
    if occurences is None:
        logmsg = "Couldn't find any occurences. Rrule: %s"
        logging.debug(logmsg, rrule)
        return None
    start_date = settings.start_date
    next_occurence = min(occurences, key=lambda x: abs(x - start_date))
    logmsg = 'Generated next occurence: (%s). Rrule: %s'
    logging.debug(logmsg, next_occurence, rrule)
    return next_occurence


def _is_skippable(settings: calview.settings.FrozenSettings,
                  event: Event) -> bool:
    """Check if event is skippable.

    Args:
        settings: full settings
        event: the event to check

    Returns:
        True: If event is skippable; False: If not

    """
    start_date = settings.start_date
    end_date = settings.end_date

    if event.status is not None:
        status = event.status.upper()
        if "CANCELLED" in status or "TENTATIVE" in status:
            logmsg = ('Suggestion: Skip: %s, status matched: "CANCELLED"'
                      ' or "TENTATIVE". Status: %s)')
            logging.info(logmsg, event.summary, event.status)
            return True
    if event.rrule is not None and event.starting is None:
        logmsg = ("Suggestion: Skip: %s; couldn't find next occurence."
                  'Rrule: %s')
        logging.info(logmsg, event.summary, event.rrule)
        return True
    # exclude non-recurrent events that, for some reason, were included in
    # the date search result
    if event.starting < start_date or event.starting > end_date:
        logmsg = ('Suggestion: Skip "%s". Starting date / time (%s)'
                  ' not between %s and %s')
        logging.info(logmsg, event.summary, event.starting, start_date,
                     end_date)
        return True
    return False
