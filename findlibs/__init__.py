#!/usr/bin/env python3
# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import ctypes.util
import os
import sys
import configparser
from pathlib import Path

__version__ = "0.0.5"

EXTENSIONS = {
    "darwin": ".dylib",
    "win32": ".dll",
}

def _get_paths_from_config():
    locations = [Path(p).expanduser() for p in [
        "~/.config/findlibs/findlibs.conf",
        "~/.findlibs",
    ]]

    locations = [p for p in locations if p.exists()]

    if len(locations) == 0: return []
    if len(locations) > 1:     
        raise ValueError(f"There are multiple config files! Delete all but one of {locations}")

    config = configparser.RawConfigParser(allow_no_value = True) # Allow keys without values
    config.optionxform = lambda option: option # Preserve case of keys 
    
    with open(locations[0], "r") as f:
        config.read(locations[0])
    
    if "Paths" not in config: return []
    # replace $HOME with ~, expand ~ to full path, 
    # resolve any relative paths to absolute paths
    paths = {Path(p.replace("$HOME", "~")).expanduser()
            for p in config["Paths"] or []}
    
    relative_paths = [p for p in paths if not p.is_absolute()]
    if relative_paths:
        raise ValueError(f"Don't use relative paths in the config file ({locations[0]}), offending paths are: {relative_paths}")
    
    files = [p for p in paths if not p.is_dir()]
    if files:
        raise ValueError(f"Don't put files in the config file ({locations[0]}), offending files are: {files}")
    

    return paths




def find(lib_name, pkg_name=None):
    """Returns the path to the selected library, or None if not found.

    Args:
        lib_name (str): Library name without the `lib` prefix
        pkg_name (str, optional): Package name if it differs from the library name.
            Defaults to None.

    Returns:
        str | None: Path to selected library
    """

    pkg_name = pkg_name or lib_name
    extension = EXTENSIONS.get(sys.platform, ".so")
    libname = "lib{}{}".format(lib_name, extension)

    # sys.prefix/lib, $CONDA_PREFIX/lib has highest priority;
    # otherwise, system library may mess up anaconda's virtual environment.

    roots = [sys.prefix]
    if "CONDA_PREFIX" in os.environ:
        roots.append(os.environ["CONDA_PREFIX"])

    for root in roots:
        for lib in ("lib", "lib64"):
            fullname = os.path.join(root, lib, libname)
            if os.path.exists(fullname):
                return fullname

    env_prefixes = [pkg_name.upper(), pkg_name.lower()]
    env_suffixes = ["HOME", "DIR"]
    envs = ["{}_{}".format(x, y) for x in env_prefixes for y in env_suffixes]

    for env in envs:
        if env in os.environ:
            home = os.path.expanduser(os.environ[env])
            for lib in ("lib", "lib64"):
                fullname = os.path.join(
                    home, lib, libname
                )
                if os.path.exists(fullname):
                    return fullname

    config_paths = _get_paths_from_config()

    for root in config_paths:
        for lib in ("lib", "lib64"):        
            filepath = root / lib / f"lib{lib_name}{extension}"
            if filepath.exists(): return str(filepath)

    for path in (
        "LD_LIBRARY_PATH",
        "DYLD_LIBRARY_PATH",
    ):
        for home in os.environ.get(path, "").split(":"):
            fullname = os.path.join(home, libname)
            if os.path.exists(fullname):
                return fullname

    for root in ("/", "/usr/", "/usr/local/", "/opt/", "/opt/homebrew/", os.path.expanduser("~/.local")):
        for lib in ("lib", "lib64"):
            fullname = os.path.join(root, lib, libname)
            if os.path.exists(fullname):
                return fullname

    return ctypes.util.find_library(lib_name)
