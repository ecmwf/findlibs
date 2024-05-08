#!/usr/bin/env python3
# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os
import sys
from pathlib import Path

import pyfakefs  # noqa registers a fixture called "fs" with pytest
import pytest

import findlibs

pkg_name = "foobar"
extension = findlibs.EXTENSIONS.get(sys.platform, ".so")
libname = f"lib{pkg_name}{extension}"

conda_prefix = "/test/conda/prefix"
os.environ["CONDA_PREFIX"] = conda_prefix
env_variable_location = os.environ[f"{pkg_name}_HOME"] = "/test/environment/variable"
ld_library_location = os.environ["LD_LIBRARY_PATH"] = "/test/ld_library/"


# A list of test locations in order of precedence
# test_find checks that if a file is placed in any of these locations then it is found
test_locations = [
    sys.prefix,
    conda_prefix,
    env_variable_location,
    "/",
    "/usr/",
    "/usr/local/",
    "/opt/",
    "/opt/homebrew/",
    os.path.expanduser("~/.local"),
]


@pytest.mark.parametrize("location", test_locations)
def test_find(fs, location):
    libpath = Path(location) / "lib" / libname
    print(f"creating {libpath}")
    fs.create_file(libpath)
    assert findlibs.find(pkg_name) == str(libpath)
