#!/usr/bin/env python3
# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import sys
from pathlib import Path

import pyfakefs  # noqa registers a fixture called "fs" with pytest
import pytest

import findlibs

extension = findlibs.EXTENSIONS.get(sys.platform, ".so")
testlib_path = f"/usr/lib/libtest{extension}"
config_paths = [
    str(Path(p).expanduser())
    for p in ["~/.config/findlibs/findlibs.conf", "~/.findlibs"]
]


def test_no_config_file(fs):
    "Check that findlibs works with no config file"
    fs.create_file(testlib_path)
    assert findlibs.find("test") == testlib_path


def test_both_config_files(fs):
    "Check that it throws an error if two config files are present"
    for p in config_paths:
        fs.create_file(p)
    with pytest.raises(ValueError):
        findlibs._get_paths_from_config()


def test_relative_path(fs):
    "Check that it throws an error on relative paths"
    fs.create_file(
        config_paths[0],
        contents="""
[Paths]
relative/path
""",
    )

    with pytest.raises(ValueError):
        findlibs._get_paths_from_config()


def test_file(fs):
    "Check that it throws an error when files are included"
    fs.create_file(
        config_paths[0],
        contents="""
[Paths]
/path/to/file.so
""",
    )

    with pytest.raises(ValueError):
        findlibs._get_paths_from_config()


def test_empty_config_file(fs):
    "Check that it works with an empty config file"
    fs.create_file(testlib_path)
    fs.create_file(config_paths[0])
    assert findlibs.find("test") == testlib_path


def test_empty_search_paths(fs):
    "Check that it works with an empty config file"
    fs.create_file(testlib_path)
    fs.create_file(
        config_paths[0],
        contents="""
[Paths]
""",
    )
    assert findlibs.find("test") == testlib_path


# Parametrised tests over
# search_dir: a path you could put into .findlibs.yml
# testlib_path: a concrete test path to check we can find tings in search_dir
@pytest.mark.parametrize(
    "search_dir,testlib_path",
    [
        ("/test/usr", f"/test/usr/lib/libtest{extension}"),  # absolute paths
        ("/test/usr", f"/test/usr/lib64/libtest{extension}"),  # lib64 aswell as lib
        (
            "~/.local",
            Path(f"~/.local/lib/libtest{extension}").expanduser(),
        ),  # ~ expansion
        (
            "$HOME/.local",
            Path(f"~/.local/lib/libtest{extension}").expanduser(),
        ),  # $HOME expansion
    ],
)
def test_config(fs, search_dir, testlib_path):
    fs.create_file(testlib_path)
    fs.create_file(
        config_paths[0],
        contents=f"""
[Paths]
{search_dir}
""",
    )
    assert findlibs.find("test") == str(testlib_path)
