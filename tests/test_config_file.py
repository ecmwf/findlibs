import pytest
import pyfakefs # registers a fixture called "fs" with pytest
import sys
import findlibs
from pathlib import Path

extension = findlibs.EXTENSIONS.get(sys.platform, ".so")
testlib_path = Path(f"/usr/lib/test{extension}")
config_path = Path(f"~/.findlibs.yml").expanduser().resolve()

def test_no_config_file(fs):
    "Check that findlibs works with no config file"
    fs.create_file(testlib_path)
    assert findlibs.find("test") == str(testlib_path)

def test_empty_config_file(fs):
    "Check that it works with an empty config file"
    fs.create_file(testlib_path)
    fs.create_file(config_path)
    assert config_path.exists()
    assert findlibs.find("test") == str(testlib_path)

def test_empty_search_paths(fs):
    "Check that it works with an empty config file"
    fs.create_file(testlib_path)
    fs.create_file(config_path, contents = 
"""
additional_search_paths:
""")

    assert config_path.exists()
    assert findlibs.find("test") == str(testlib_path)

# Parametrised tests over
# search_dir: a path you could put into .findlibs.yml
# testlib_path: a concrete test path to check we can find tings in search_dir
@pytest.mark.parametrize("search_dir,testlib_path", [
                ("/test/usr", f"/test/usr/lib/libtest{extension}"), # absolute paths
                ("/test/usr", f"/test/usr/lib64/libtest{extension}"), # lib64 aswell as lib
                ("~/.local", Path(f"~/.local/lib/libtest{extension}").expanduser()), # ~ expansion
                ("$HOME/.local", Path(f"~/.local/lib/libtest{extension}").expanduser()), # $HOME expansion
])
def test_config(fs, search_dir, testlib_path):

    fs.create_file(testlib_path)
    fs.create_file(config_path, contents = 
f"""
additional_search_paths:
  - {search_dir}
""")
    assert findlibs.find("test") == str(testlib_path)
    