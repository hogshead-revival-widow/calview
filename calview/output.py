#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Defines all output-related functions. Cf. calview.templates
(in CONFIG_DIR) for output templates.

Usage:
    output = get_output(settings, events)
    put_out(settings, output)

"""

import collections
import logging
import typing
import calview.events
import calview.settings
import calview.helper


def put_out(settings: calview.settings.FrozenSettings, output: str) -> None:
    """Print or write final output.

    Args:
        settings: full settings
        output: the final output, as returned by
        calview.output.get_output

    """
    if settings.output_to_file and settings.output_file is not None:
        with open(settings.output_file, 'w') as output_file:
            output_file.write(output)
    else:
        print(output)


def get_output(settings: calview.settings.FrozenSettings,
               events: collections.OrderedDict) -> str:
    """Assembles final output.

    Args:
        settings: full settings
        events: all events, as returned by calview.events.get_events

    Returns:
        Output
    """
    single, recurrent = _render_events(settings, events)
    output = _render_output(settings, single, recurrent)
    return output


def _render_events(settings: calview.settings.FrozenSettings,
                   event_dict: dict) -> tuple:
    """
    Render all events.

    Args:
        settings: full settings
        event_dict: sorted events

    Returns:
        Tuple with the following elements:
            (1) All single events rendered as one string.
            (2) All recurrent events rendered as one string.

    """
    events = collections.OrderedDict()
    recurrent = collections.OrderedDict()
    for header, listed_events in event_dict.items():
        events[header] = list()
        recurrent[header] = list()
        for event in listed_events:
            if event.rrule is None:
                single = _render_single(settings, event)
                events[header].append(single)
            else:
                recc = _render_recurrent(settings, event)
                recurrent[header].append(recc)
    out_events = ''
    out_recurrent = ''
    for header, listed_events in events.items():
        if len(listed_events) < 1:
            continue
        out_events = out_events + \
            header + '\n'.join(listed_events)
    for header, listed_events in recurrent.items():
        if len(listed_events) < 1:
            continue
        out_recurrent = out_recurrent + \
            header + '\n'.join(listed_events)
    return out_events, out_recurrent


def _render_output(settings: calview.settings.FrozenSettings, events: str,
                   recurrent: str) -> str:
    """Putting all events in the final templates.

    Arg:
        settings: full settings
        events: all single events, fully formatted
        recurrent: all recurrent events, fully formatted

    Returns:
        Rendered events in final template in one string.

    """
    full = calview.helper.get_template(settings, 'full')
    without_recc = calview.helper.get_template(settings, 'full_without_recc')

    if len(recurrent) < 1:
        return without_recc.format(events=events)
    return full.format(events=events, recurrent=recurrent)


# todo: the "rendered" rrule is as of now only comprehensive because
# it relies on contextual informations in the output format; they
# should be comprehensible as one stand-alone sentence.
def _render_rrule(settings: calview.settings.FrozenSettings,
                  event: calview.events.Event) -> typing.Union[str, dict]:
    """Translates rrule to settings.language (with a very limited
    support of rrule's elements).

    For now, only these RRULE tags are regarded: INTERVAL, FREQ and in
    combination with the above: UNTIL, COUNT.

    Args:
        settings: full settings
        event: the recurrent calview event to render

    Returns:
        The translation (if successfull, otherwise the raw rrule string);
        if additional information is added (e. g. the next occurences)
        a dict is returned (keys: "translation", "additional");
        otherwise a string is returned

    Todo:
        (1): The translation isn't working very well right now and not
        covering A LOT. For the intended purprose, it seems to suffice.
        Sadly, there is no (?) comprehensive python library to translate
        rrule to natural language; there is, however:
        https://github.com/jakubroztocil/rrule.
        (2): This is quite hacky; I should use datetutil.rrule for
        parsing as they deliver a tested, feature-complete (as it seems)
        pythonic representation of a rrule; i.e. this should be the basis
        for any proper translation.

    """
    rrule = event.rrule
    rrule = (rule.lower().split('=') for rule in rrule.split(";"))
    rrule = {rule[0]: rule[1] for rule in rrule}
    where = 'singular'
    translation = ""
    if 'interval' in rrule and int(rrule['interval']) > 1:
        where = 'plural'
        recurrance = rrule['interval']
    if 'freq' in rrule:
        translation_map = calview.helper.get_template(
            settings, 'rrule_translation_map')
        translation = translation_map[where][rrule['freq']]
        if where == 'plural':
            # e.g: every {interval} days
            translation = translation.format(recurrance)
        if 'until' in rrule or 'count' in rrule:
            occurences = calview.events.get_occurences(settings,
                                                       event.starting,
                                                       event.rrule,
                                                       include_after_end_date=True)
            # occurence includes the original event
            # so a (valid) repetition is only: len(occurences)+1
            if occurences is not None and len(occurences) > 1:
                translation = dict(frequence=translation)
                day_format = calview.helper.get_template(
                    settings, 'day_format')
                repeat_times = len(occurences) - 1
                if repeat_times == 1:
                    date = occurences[1].strftime(day_format)
                    repeat = translation_map['limited_repeat']['once']
                    repeat = repeat.format(date)
                    translation['additional'] = repeat
                else:
                    last = occurences[-1].strftime(day_format)
                    howmany = 'many'
                    if repeat_times <= 3:
                        howmany = 'few'
                    repeat = translation_map['limited_repeat'][howmany]
                    repeat = repeat.format(last)
                    translation['additional'] = repeat
        logmsg = 'Tried a translation for: "%s", check rrule: %s.'
        logging.info(logmsg, event.summary, event.rrule)
    if len(translation) > 0:
        return translation
    logmsg = ('Translation failed (occurence frequence) for: "%s". '
              'Including raw rrule string in output.')
    logging.warning(logmsg, event.summary)
    return event.rrule


def _render_starttime(settings: calview.settings.FrozenSettings,
                      event: calview.events.Event) -> str:
    """
    Renders starttime of an event.

    This is done according to calview.templates `starting_fullday` or
    or `starting_time` respectivly.

    Args:
        settings: full settings
        event: event whose start time should be rendered

    Returns:
        Rendered start time of an event.

    """
    if event.is_fullday:
        out = calview.helper.get_template(settings, 'starting_fullday')
    else:
        out_date = calview.helper.get_template(settings, 'starting_time')
        out = event.starting.strftime(out_date)
    return out


def _render_recurrent(settings: calview.settings.FrozenSettings,
                      event: calview.events.Event) -> str:
    """Renders recurrent event to str.

    This is done according to `event_recurrent`, `event_more`,
    `event_epilog` templates defined in calview.templates.

    Args:
        * settings: full settings
        * event: event whose start time should be rendered

    Returns:
        * out: rendered event

    """
    recurrent = calview.helper.get_template(settings, 'event_reccurent')
    more = calview.helper.get_template(settings, 'event_more')
    epilog = calview.helper.get_template(settings, 'event_epilog')
    start = _render_starttime(settings, event)
    frequence = _render_rrule(settings, event)
    format_args = dict(frequence=frequence, starting=start,
                       summary=event.summary, location=event.location)
    if isinstance(frequence, dict):
        recc_added = 'event_reccurent_occurences_added'
        recurrent = calview.helper.get_template(settings, recc_added)
        format_args['additional'] = frequence['additional']
        format_args['frequence'] = frequence['frequence']
    out = recurrent.format(**format_args)
    if event.more is not None:
        sep = calview.helper.get_template(settings, 'event_more_item_sep')
        text = f'\n{sep} '.join(event.more.strip().split('\n'))
        out = out + more.format(text=text)
    out = out + epilog
    return out


def _render_single(settings: calview.settings.FrozenSettings,
                   event: calview.events.Event) -> str:
    """Renders single event to str.

    This is done according to `event_single`, `event_more`,
    `event_epilog` templates defined in calview.templates.

    Args:
    settings: full settings
    event: event whose start time should be rendered

    Returns:
        Rendered event

    """
    single = calview.helper.get_template(settings, 'event_single')
    more = calview.helper.get_template(settings, 'event_more')
    epilog = calview.helper.get_template(settings, 'event_epilog')
    start = _render_starttime(settings, event)
    out = single.format(
        starting=start,
        summary=event.summary,
        location=event.location)
    if event.more is not None:
        text = '\n** '.join(event.more.strip().split('\n'))
        out = out + more.format(text=text)
    out = out + epilog
    return out
