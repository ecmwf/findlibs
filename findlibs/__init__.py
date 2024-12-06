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
import os
import sys
from pathlib import Path

__version__ = "0.0.5"

EXTENSIONS = {
    "darwin": ".dylib",
    "win32": ".dll",
}


def _find_in_package(lib_name: str, pkg_name: str) -> str | None:
    """Tries to find the library in an installed python module `{pgk_name}libs`.
    This is a convention used by, for example, by newly built binary-only ecmwf
    packages, such as eckit dlibs in the "eckitlib" python module."""
    # NOTE we could have searched for relative location wrt __file__ -- but that
    # breaks eg editable installs of findlibs, conda-venv combinations, etc.
    # The price we pay is that the binary packages have to be importible, ie,
    # the default output of auditwheel wont work
    try:
        module = importlib.import_module(pkg_name + "libs")
        venv_wheel_lib = str((Path(module.__file__) / ".." / lib_name).resolve())
        if os.path.exists(venv_wheel_lib):
            return venv_wheel_lib
    except ImportError:
        pass
    return None


def _find_in_python(lib_name: str, pkg_name: str) -> str | None:
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


def _find_in_home(lib_name: str, pkg_name: str) -> str | None:
    env_prefixes = [pkg_name.upper(), pkg_name.lower()]
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


def _find_in_config_paths(lib_name: str, pkg_name: str) -> str | None:
    paths = _get_paths_from_config()
    for root in paths:
        for lib in ("lib", "lib64"):
            filepath = root / lib / lib_name
            if filepath.exists():
                return str(filepath)
    return None


def _find_in_ld_path(lib_name: str, pkg_name: str) -> str | None:
    for path in (
        "LD_LIBRARY_PATH",
        "DYLD_LIBRARY_PATH",
    ):
        for home in os.environ.get(path, "").split(":"):
            fullname = os.path.join(home, lib_name)
            if os.path.exists(fullname):
                return fullname
    return None


def _find_in_sys(lib_name: str, pkg_name: str) -> str | None:
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


def _find_in_ctypes_util(lib_name: str, pkg_name: str) -> str | None:
    return ctypes.util.find_library(lib_name)


def find(lib_name: str, pkg_name: str | None = None) -> str | None:
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
        Package name if it differs from the library name. Defaults to None.

    Returns
    --------
    str or None
        Path to selected library
    """
    pkg_name = pkg_name or lib_name
    extension = EXTENSIONS.get(sys.platform, ".so")
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
        if result := source(lib_name, pkg_name):
            return result
    return None
