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

__version__ = "0.0.2"


EXTENSIONS = {
    "darwin": ".dylib",
    "win32": ".dll",
}


def find(libname, pkgname=None):
    """
    Returns the path to the selected library, or None if not found.

    Parameters:
        libname(str): Name of the library, excluding "lib" prefix
        pkgname(str, optional): Name of the package, if different than name of
            the library.

    Returns:
        str: Path to the library
    """

    extension = EXTENSIONS.get(sys.platform, ".so")
    pkgname = pkgname or libname

    for what in ("HOME", "DIR"):
        envs = [
            "{}_{}".format(pkgname.upper(), what),
            "{}_{}".format(pkgname.lower(), what),
        ]
        for env in envs:
            if env in os.environ:
                home = os.environ[env]
                for lib in ("lib", "lib64"):
                    fullname = os.path.join(
                        home, lib, "lib{}{}".format(libname, extension)
                    )
                    if os.path.exists(fullname):
                        return fullname

    for path in (
        "LD_LIBRARY_PATH",
        "DYLD_LIBRARY_PATH",
    ):
        for home in os.environ.get(path, "").split(":"):
            fullname = os.path.join(home, "lib{}{}".format(libname, extension))
            if os.path.exists(fullname):
                return fullname

    for root in ("/", "/usr/", "/usr/local/", "/opt/"):
        for lib in ("lib", "lib64"):
            fullname = os.path.join(
                root, lib, "lib{}{}".format(libname, extension)
            )
            if os.path.exists(fullname):
                return fullname

    return ctypes.util.find_library(libname)
