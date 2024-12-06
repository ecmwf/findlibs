import os
import sys
from pathlib import Path

from findlibs import DYLIB_PATH, find


def test_transitive() -> None:
    """There is a module modAlibs in this directory that mocks expected bin wheel contract:
     - modulename ends with 'libs'
     - contains libmodA.so
     - inside __init__ there is the findlibs_dependencies, containing modBlibs
    This test checks that when such module is findlibs-found, it extend the platform's dylib
    env var with the full path to the modBlibs module
    """

    sys.path.append(str(Path(__file__).parent))

    found = find("modA")
    expected_found = str(Path(__file__).parent / "modAlibs" / "libmodA.so")
    assert found == expected_found

    expected_dylib = str(Path(__file__).parent / "modBlibs")
    assert expected_dylib in os.environ[DYLIB_PATH[sys.platform]]
