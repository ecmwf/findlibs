import sys
from pathlib import Path

import findlibs


def test_transitive(monkeypatch) -> None:
    """There is a module modAlibs in this directory that mocks expected bin wheel contract:
     - modulename ends with 'libs'
     - contains libmodA.so
     - inside __init__ there is the findlibs_dependencies, containing modBlibs
    This test checks that when such module is findlibs-found, it extend the platform's dylib
    env var with the full path to the modBlibs module
    """

    # so that modAlibs and modBlibs are visible
    sys.path.append(str(Path(__file__).parent))

    # the files in test are not real .so, we thus just track what got loaded
    loaded_libs = set()

    def libload_accumulator(path: str):
        loaded_libs.add(path)

    monkeypatch.setattr(findlibs, "CDLL", libload_accumulator)

    # test
    found = findlibs.find("modA")
    expected_found = str(Path(__file__).parent / "modAlibs" / "lib64" / "libmodA.so")
    assert found == expected_found

    expected_dylib = str(Path(__file__).parent / "modBlibs" / "lib64" / "libmodB.so")
    assert loaded_libs == {expected_dylib}
