import sys
from pathlib import Path

import findlibs


def test_transitive(monkeypatch) -> None:
    """There is a module modAlibs in this directory that mocks expected bin wheel contract:
     - modulename ends with 'lib'
     - contains libmodA.so
     - inside __init__ there is the findlibs_dependencies, containing modBlib
    This test checks that when such module is findlibs-found, the (mock) ld loaded the libmodB
    """

    # so that modAlibs and modBlibs are visible
    sys.path.append(str(Path(__file__).parent))

    # the files in test are not real .so, we thus just track what got loaded
    loaded_libs = set()

    def libload_accumulator(path: str):
        loaded_libs.add(path)

    monkeypatch.setattr(findlibs, "CDLL", libload_accumulator)
    monkeypatch.setattr(
        sys, "platform", "tests"
    )  # this makes the test behave like linux default

    # test
    found = findlibs.find("modA")
    expected_found = str(Path(__file__).parent / "modAlib" / "lib64" / "libmodA.so")
    assert found == expected_found

    expected_dylib = str(Path(__file__).parent / "modBlib" / "lib64" / "libmodB.so")
    assert loaded_libs == {expected_dylib}
