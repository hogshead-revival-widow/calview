#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Output and rendering templates defaults.
calview.__init__ copies this to calview.settings.TEMPLATE_PATH."""

# final output templates (FULL, FULL_WITHOUT_RECC)
de_full = '''
ALLE VERANSTALTUNGEN

Eine Chance:

{events}

Regelmäßig:

{recurrent}
'''

de_full_without_recc = '''
ALLE VERANSTALTUNGEN

EINE CHANCE

{events}
'''


de_rrule_translation_map = {
    # events that repeat according to INTERVAL
    'plural': {
        'daily': 'jeden {}. Tag',
        'weekly': 'jede {}. Woche',
        'monthly': 'jeden {}. Monat',
        'yearly': 'jedes {}. Jahr'
    },
    # events that repeat according to FREQ
    'singular': {
        'daily': 'täglich',
        'weekly': 'wöchentlich',
        'monthly': 'monatlich',
        'yearly': 'jährlich',
    },
    # events that repeat but only COUNT times or UNTIL date
    # 'few' and 'many' are combined with one of 'plural' / 'singular'
    'limited_repeat': {
        # event with only 1 repetition
        'once': 'nur noch einmal am {}',
        # event with up to 3 repeats
        'few': '(letztes Mal: {})',
        # event with more than 3 repeats
        'many': '(bis: {})'
    }
}

de_day_format = '%a, %d.%m'

de_recc_occ_added = ('[x] {starting}: {summary} \n[xx] weitere Termine:'
                     ' {frequence} \n[xx] {location}')

templates = dict()
templates['de_DE'] = dict(
    # format of start time output (if not fullday event)
    starting_time='ab %H:%M',
    # day_format
    day_format=de_day_format,
    # collective header (all events that start at this date are summarized under this)
    day_header='\n' + de_day_format + '\n',  # must be usable as dict key
    # see above explanation for the following
    full=de_full,
    full_without_recc=de_full_without_recc,
    rrule_translation_map=de_rrule_translation_map,
    # format of start date output (if fullday event)
    starting_fullday='den ganzen Tag lang',
    # base template for non-reccurent event
    event_single='[x] {starting}: {summary} \n[xx] {location}',
    # base template reccurrent event
    event_reccurent='[x] {frequence}, {starting}: {summary} \n[xx] {location}',
    event_reccurent_occurences_added=de_recc_occ_added,
    # additional template, may be coupled with `SINGLE_EVENT` and / or `RECC_EVENT`
    event_more='\n[xx] more: {text}',
    event_more_item_sep='[xx]',
    # added after every event
    event_epilog='\n'
)
