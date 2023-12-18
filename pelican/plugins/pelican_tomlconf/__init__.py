"""
Pelican TomlConf

"""
##-- builtin imports
## Standard imports i keep having to import, as an auto snippet
from __future__ import annotations

import abc
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time # for sleep()
import types
import collections
import contextlib               # stdlib. https://docs.python.org/3/library/contextlib.html
import hashlib
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from uuid import UUID, uuid1
from weakref import ref # https://docs.python.org/3/library/weakref.html#module-weakref
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)

import atexit # for @atext.register
import faulthandler             # stdlib. https://docs.python.org/3/library/faulthandler.html
##-- end builtin imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

import tomlguard as TG
from pelican import signals

CONFIG_FILENAME   = pl.Path("pelican.toml")
FALLBACK_FILENAME = pl.Path("pyproject.toml")

def apply_section(section, settings):
    for key,value in section.items():
        if not key.isupper():
            continue
        logging.debug("Updating: %s : %s -> %s", key, settings.get(key, None), value)
        settings[key] = value

def apply_paths(section, settings):
    for key,value in section.items():
        if not key.isupper():
            continue
        logging.debug("Updating: %s : %s -> %s", key, settings.get(key, None), value)
        settings[key] = pl.Path(value).expanduser().resolve()


def pelican_read_toml(sender):
    data = None
    if CONFIG_FILENAME.exists():
        data                    = TG.load(CONFIG_FILENAME)
    elif FALLBACK_FILENAME.exists():
        data                = TG.load(FALLBACK_FILENAME).on_fail(None).tool.pelican()

    if data is None:
        return

    apply_paths(data.paths,                    sender.settings)

    apply_section(data.pelican,                sender.settings)
    apply_section(data.site.setup,             sender.settings)
    apply_section(data.site.static,            sender.settings)
    apply_section(data.site.articles,          sender.settings)
    apply_section(data.site.pages,             sender.settings)
    apply_section(data.site.theme,             sender.settings)
    apply_section(data.site.templates,         sender.settings)
    apply_section(data.rst,                    sender.settings)
    apply_section(data.markdown,               sender.settings)
    apply_section(data.build.core,             sender.settings)
    apply_section(data.build.options,          sender.settings)
    apply_section(data.jinja,                  sender.settings)
    apply_section(data.logging,                sender.settings)
    apply_section(data.typogrify,              sender.settings)
    apply_section(data.slugify,                sender.settings)
    apply_section(data.cache,                  sender.settings)
    apply_section(data.site.settings,          sender.settings)
    apply_section(data.site.settings.datetime, sender.settings)

    for section in data.site.urls:
        apply_section(section, sender.settings)

    # Normalize Paths:
    # path, output_path, theme, cache_path
    if not sender.settings['THEME'].exists():
        sender.settings['THEME']       = data.site.theme

    sender.path                        = sender.settings['PATH']
    sender.output_path                 = sender.settings['OUTPUT_PATH']
    sender.theme                       = sender.settings['THEME']
    sender.ignore_files                = sender.settings["IGNORE_FILES"]
    sender.delete_outputdir            = sender.settings["DELETE_OUTPUT_DIRECTORY"]
    sender.output_retention            = sender.settings["OUTPUT_RETENTION"]
    sender.init_path()

    return


def register():
    signals.initialized.connect(pelican_read_toml)
