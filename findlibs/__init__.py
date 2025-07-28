#!/usr/bin/env python3
# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import configparser
import ctypes.util
import importlib
import logging
import os
import re
import sys
import warnings
from collections import defaultdict
from ctypes import CDLL, RTLD_GLOBAL
from pathlib import Path
from types import ModuleType
from typing import Union

__version__ = "0.1.2"

logger = logging.getLogger(__name__)

EXTENSIONS = defaultdict(
    lambda: ".so",
    darwin=".dylib",
    win32=".dll",
)
EXTENSIONS_RE = defaultdict(
    lambda: r"^.*\.so(.[0-9]+)?$",
    darwin=r"^.*\.dylib$",
    win32=r"^.*\.dll$",
)


def _load_globally(path: str) -> CDLL:
    """Loads the library to make it accessible to subsequently loaded libraries and extensions"""
    # NOTE this doesnt ultimately work on MacOS -- without corresponding `rpath`s on the lib, we end up
    # failing asserts in `eckit::system::LibraryRegistry::enregister`. Possibly, fixing that assert,
    # making library names correct, etc, could make this work
    return CDLL(path, mode=RTLD_GLOBAL)


def _single_preload_deps(path: str) -> None:
    """See _find_in_package"""
    logger.debug(f"initiating recursive search at {path}")
    for lib in os.listdir(path):
        logger.debug(f"considering {lib}")
        if re.match(EXTENSIONS_RE[sys.platform], lib):
            logger.debug(f"loading {lib} at {path}")
            _ = _load_globally(f"{path}/{lib}")
            logger.debug(f"loaded {lib}")


def _transitive_preload_deps(module: ModuleType) -> None:
    """See _find_in_package"""
    # NOTE consider replacing hasattr with entrypoint-based declaration
    # https://packaging.python.org/en/latest/specifications/entry-points/
    if hasattr(module, "findlibs_dependencies"):
        for module_name in module.findlibs_dependencies:
            logger.debug(f"consider transitive dependency preload of {module_name}")
            try:
                rec_into = importlib.import_module(module_name)
                # NOTE we need *first* to evaluate recursive call, *then* preload,
                # to ensure that dependencies are already in place
                _transitive_preload_deps(rec_into)

                for ext_path in (
                    str(Path(rec_into.__file__).parent / "lib"),
                    str(Path(rec_into.__file__).parent / "lib64"),
                ):
                    if os.path.exists(ext_path):
                        _single_preload_deps(ext_path)
            except ImportError:
                # NOTE we don't use ImportWarning here as thats off by default
                m = f"unable to import {module_name} yet declared as dependency of {module.__name__}"
                warnings.warn(m)
                logger.debug(m)


def _find_in_package(
    lib_name: str, pkg_name: str, preload_deps: Union[bool, None] = None
) -> Union[str, None]:
    """Tries to find the library in an installed python module `{pgk_name}`.
    Examples of packages with such expositions are `eckitlib` or `odclib`.

    If preload deps is True, it additionally opens all dylibs of this library and its
    transitive dependencies This is needed if the `.so`s in the wheel don't have
    correct rpath -- which is effectively impossible in non-trivial venvs.

    It would be tempting to just extend LD_LIBRARY_PATH -- alas, that won't have any
    effect as the linker has been configured already by the time cpython is running"""
    if preload_deps is None:
        preload_deps = (
            sys.platform != "darwin"
        )  # NOTE see _load_globally for explanation
    try:
        module = importlib.import_module(pkg_name)
        logger.debug(f"found package {pkg_name}; with {preload_deps=}")
        if preload_deps:
            _transitive_preload_deps(module)
        for venv_wheel_lib in (
            str((Path(module.__file__).parent / "lib" / lib_name)),
            str((Path(module.__file__).parent / "lib64" / lib_name)),
        ):
            if os.path.exists(venv_wheel_lib):
                return venv_wheel_lib
    except ImportError:
        pass
    return None


def _find_in_python(lib_name: str, pkg_name: str) -> Union[str, None]:
    """Tries to find the library installed directly to Conda/Python sys.prefix
    libs"""
    roots = [sys.prefix]
    if "CONDA_PREFIX" in os.environ:
        roots.append(os.environ["CONDA_PREFIX"])

    for root in roots:
        for lib in ("lib", "lib64"):
            fullname = os.path.join(root, lib, lib_name)
            if os.path.exists(fullname):
                return fullname
    return None


def _find_in_home(lib_name: str, pkg_name: str) -> Union[str, None]:
    env_prefixes = [pkg_name.upper(), pkg_name.lower()]
    if pkg_name.endswith("lib"):
        # if eg "eckitlib" is pkg name, consider also "eckit" prefix
        env_prefixes += [pkg_name.upper()[:-3], pkg_name.lower()[:-3]]
    env_suffixes = ["HOME", "DIR"]
    envs = ["{}_{}".format(x, y) for x in env_prefixes for y in env_suffixes]

    for env in envs:
        if env in os.environ:
            home = os.path.expanduser(os.environ[env])
            for lib in ("lib", "lib64"):
                fullname = os.path.join(home, lib, lib_name)
                if os.path.exists(fullname):
                    return fullname
    return None


def _get_paths_from_config():
    locations = [
        Path(p).expanduser()
        for p in [
            "~/.config/findlibs/findlibs.conf",
            "~/.findlibs",
        ]
    ]

    locations = [p for p in locations if p.exists()]

    if len(locations) == 0:
        return []
    if len(locations) > 1:
        raise ValueError(
            f"There are multiple config files! Delete all but one of {locations}"
        )

    config = configparser.RawConfigParser(
        allow_no_value=True
    )  # Allow keys without values
    config.optionxform = lambda option: option  # Preserve case of keys

    with open(locations[0], "r"):
        config.read(locations[0])

    if "Paths" not in config:
        return []
    # replace $HOME with ~, expand ~ to full path,
    # resolve any relative paths to absolute paths
    paths = {Path(p.replace("$HOME", "~")).expanduser() for p in config["Paths"] or []}

    relative_paths = [p for p in paths if not p.is_absolute()]
    if relative_paths:
        raise ValueError(
            (
                f"Don't use relative paths in the config file ({locations[0]}),"
                f" offending paths are: {relative_paths}"
            )
        )

    files = [p for p in paths if not p.is_dir()]
    if files:
        raise ValueError(
            f"Don't put files in the config file ({locations[0]}), offending files are: {files}"
        )

    return paths


def _find_in_config_paths(lib_name: str, pkg_name: str) -> Union[str, None]:
    paths = _get_paths_from_config()
    for root in paths:
        for lib in ("lib", "lib64"):
            filepath = root / lib / lib_name
            if filepath.exists():
                return str(filepath)
    return None


def _find_in_ld_path(lib_name: str, pkg_name: str) -> Union[str, None]:
    for path in (
        "LD_LIBRARY_PATH",
        "DYLD_LIBRARY_PATH",
    ):
        for home in os.environ.get(path, "").split(":"):
            fullname = os.path.join(home, lib_name)
            if os.path.exists(fullname):
                return fullname
    return None


def _find_in_sys(lib_name: str, pkg_name: str) -> Union[str, None]:
    for root in (
        "/",
        "/usr/",
        "/usr/local/",
        "/opt/",
        "/opt/homebrew/",
        os.path.expanduser("~/.local"),
    ):
        for lib in ("lib", "lib64"):
            fullname = os.path.join(root, lib, lib_name)
            if os.path.exists(fullname):
                return fullname
    return None


def _find_in_ctypes_util(lib_name: str, pkg_name: str) -> Union[str, None]:
    # NOTE this is a bit unreliable function, as for some libraries/sources,
    # it returns full path, in others just a filename. It still may be worth
    # it as a fallback even in the filename-only case, to help troubleshoot some
    # yet unknown source
    return ctypes.util.find_library(lib_name) or ctypes.util.find_library(
        lib_name.removeprefix("lib")
    )


def find(lib_name: str, pkg_name: Union[str, None] = None) -> Union[str, None]:
    """Returns the path to the selected library, or None if not found.
    Searches over multiple sources in this order:
      - importible python module ("PACKAGE")
      - python's sys.prefix and conda's libs ("PYTHON")
      - package's home like ECCODES_HOME ("HOME")
      - findlibs config like .findlibs ("CONFIG_PATHS")
      - ld library path ("LD_PATH")
      - system's libraries ("SYS")
      - invocation of ctypes.util ("CTYPES_UTIL")
    each can be disabled via setting FINDLIBS_DISABLE_{method} to "yes",
    so eg `export FINDLIBS_DISABLE_PACKAGE=yes`. Consult the code for each
    individual method implementation and further configurability.

    Arguments
    ---------
    lib_name : str
        Library name without the `lib` prefix. The name of the library to
        find is formed using ``lib_name`` and a platform specific suffix
        (by default ".so"). E.g. when ``lib_name`` is "eccodes" the library
        name will be "libeccodes.so" on Linux and "libeccodes.dylib"
        on macOS.
    pkg_name :  str, optional
        Package name if it differs from the library name. Defaults to None,
        which sets it to f"{lib_name}lib". Used by python module import and
        home sources, with the home source considering also `lib`-less name.

    Returns
    --------
    str or None
        Path to selected library
    """
    pkg_name = pkg_name or f"{lib_name}lib"
    extension = EXTENSIONS[sys.platform]
    lib_name = "lib{}{}".format(lib_name, extension)

    sources = (
        (_find_in_package, "PACKAGE"),
        (_find_in_python, "PYTHON"),
        (_find_in_home, "HOME"),
        (_find_in_config_paths, "CONFIG_PATHS"),
        (_find_in_ld_path, "LD_PATH"),
        (_find_in_sys, "SYS"),
        (_find_in_ctypes_util, "CTYPES_UTIL"),
    )
    sources_filtered = (
        source_clb
        for source_clb, source_name in sources
        if os.environ.get(f"FINDLIBS_DISABLE_{source_name}", None) != "yes"
    )

    for source in sources_filtered:
        logger.debug(f"about to search for {lib_name}/{pkg_name} in {source}")
        if result := source(lib_name, pkg_name):
            logger.debug(f"found {lib_name}/{pkg_name} in {source}")
            return result
    return None


def load(lib_name: str, pkg_name: Union[str, None] = None) -> CDLL:
    """Convenience method to find a library and load it right away (recursively)"""
    path = find(lib_name, pkg_name)
    if not path:
        raise ValueError(f"unable to find {pkg_name+'.' if pkg_name else ''}{lib_name}")
    else:
        return _load_globally(path)
