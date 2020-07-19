#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check and if neccessary create required files; expand this modules
namespace to `calview.settings.CONFIG_DIR`.

Checks if all required files and directories are present in
`calview.settings.CONFIG_DIR` and if SETTINGS_DEFAULTS is complete.

Required are:
        * directory: CONFIG_DIR
        * inside this directory:
            * file: calview.settings.TEMPLATE_FILE_NAME
            * file: calview.settings.SETTINGS_FILE_NAME

If required files are not present, they are not present, create them:
  by copying calview.settings.TEMPLATE_FILE_NAME in
  calview.settings.DATA_DIR to calview.settings.CONFIG_DIR
  by creating the settings file according to SETTINGS_DEFAULTS.

"""

import os
import sys
import shutil
import configparser
from calview.settings import (CONFIG_DIR, DATA_DIR,
                              TEMPLATE_FILE_NAME,
                              SETTINGS_FILE_NAME,
                              TEMPLATE_PATH,
                              SETTINGS_PATH,
                              SETTINGS_DEFAULTS,
                              SETTINGS_HELPMSG)


def _setup_calview() -> None:
    """Create needed files, if not present.

    This is encansuplated inside a function to ensure no weird
    site effects, as __init__ is senitive.

    """
    if not os.path.isdir(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)
    if not os.path.isfile(TEMPLATE_PATH):
        shutil.copy(os.path.join(DATA_DIR, TEMPLATE_FILE_NAME),
                    CONFIG_DIR)
    if not os.path.isfile(SETTINGS_PATH):
        config = configparser.ConfigParser()
        config.read_dict(SETTINGS_DEFAULTS)
        with open(SETTINGS_PATH, 'w') as file:
            file.write(SETTINGS_HELPMSG)
            config.write(file)


_setup_calview()

# add CONFIG_DIR to this modules' namespace
if os.path.exists(CONFIG_DIR):
    __path__.append(CONFIG_DIR)
