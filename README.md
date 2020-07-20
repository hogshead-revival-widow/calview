# Readme

## Description

Console script `calviewer` to generate text output based on a
CalDAV-accessible calendar. 

## Configuration

*Notice*: Before installation, put your username, CalDAV server and the URL of 
the calendar you want to query in: *calview/calview/connection.py* 

After installation and first run, set your configuration in `~/.calview` (see below). 

(On Windows, `USERPROFILE\calview` is used if `USERPROFILE` is set, otherwise a combination of `HOMEPATH` and `HOMEDRIVE`.)

## Installation

1. Before installation, make sure to read the *configuration* section (above).
2. Clone or download repo.
3. CD to the directory enclosing the repo.
4. Run: `pip install calview/`

*Notice*: On a Mac / with homebrewed python you might need to run `pip3` instead.

This makes `calviewer` available as a console script.

## Requirements

See `calview/setup.py`

## Usage

`calviewer 01012020` (DDMMYYYY)

This lists the events from 01012020 to 15012020.

Alternatively, you can set an end date: `calviewer 01012020 -e 01032020` (DDMMYYYY).

There are more options: `calviewer -h`.

### Settings, Templates

You can change the output templates in `~/.calview/templates.py` and the default behavior in `~/.calview/settings.ini`.
If you don't see `~/.calview`, run `calviewer`. The directory and files are not created before the first run. 

(On Windows, `USERPROFILE\calview` is used if USERPROFILE is set, otherwise a combination of `HOMEPATH` and `HOMEDRIVE`.)


## Limitations

Limitations:

* This has only been tested for personal use.
* It's been only tested with nextcloud.
* RRULE translation to natural language is not very comprehensive right now. See `_render_rrule` in `calview/calview/output.py`. 
  * For now, only the following elements are (well, a little bit) supported:
    * UNTIL,
    * FREQUENCE,
    * INTERVAL
    * *Notice*: There may be cases where the proper recurrence rule is swallowed. See the log for all inspected rrules. If it clearly can't be translated, the raw rrule is included in the output.

## Assumptions

It is assumed that an event has (at least) a value for the following VEVENT properties:

* DTSTART,
* SUMMARY,
* LOCATION





