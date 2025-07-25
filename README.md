# findlibs

A Python package that searches for shared libraries on various platforms.


## Usage

```python
import findlibs
lib = findlibs.find("eccodes")

# If package name differs from library name use:
lib = findlibs.find(lib_name="odccore", pkg_name="odc")
```

## Installation

```bash
pip install findlibs
```

## Testing

```bash
git clone https://github.com/ecmwf/findlibs
cd findlibs
pip install -e ".[test]"
pytest
```

## find

The module only contains the `find()` function.

```python
def find(lib_name, pkg_name=None)
```

Returns the path to the selected library, or None if not found.

**Arguments**:

- `lib_name` _str_ - Library name without the `lib` prefix. The name of the library to find is formed using `lib_name` and a platform specific suffix (by default ".so"). E.g. when `lib_name` is "eccodes" the library name will be "libeccodes.so" on Linux and "libeccodes.dylib" on macOS.
- `pkg_name` _str, optional_ - Package name if it differs from the library name.

  
**Returns**:

  str or None: Path to selected library

The **algorithm** to find the library is as follows:

- First, tries to find the library in an installed python module package
  with the given name, e.g. eccodeslib, eckitlib. Disable this search
  option by setting environment variable `FINDLIBS_DISABLE_PACKAGE=yes`.

- Next, tries the `lib` and `lib64` directories under `sys.prefix` and `$CONDA_PREFIX`. Disable this search option by setting environment variable `FINDLIBS_DISABLE_PYTHON=yes`.

- Next, tries the `lib` and `lib64` directories under the paths defined by the `pkg_name + "_HOME"` and `pkg_name + "_DIR"` environment variables. Both lowercase and uppercase versions are tested. E.g. if `pkg_name` is "eccodes" it will check the paths defined by `$eccodes_dir`, `$eccodes_home`, `$ECCODES_DIR` and `$ECCODES_HOME`. Disable this search option by setting environment variable `FINDLIBS_DISABLE_HOME=yes`.

- Next, tries to load the search paths from the user defined `~/.findlibs` or `~/.config/findlibs/findlibs.conf` INI configuration files. Then for all the user defined search paths, the `lib` and `lib64` subdirectories are tried. 

    Please note that only one of these files can exist. The configuration file can contain multiple search paths, but no relative paths or paths to files are allowed. The file can even be completely empty or can contain no paths at all. The file format is as follows:

    ```
    [Paths]
    /path/to/lib_directory
    ```
  Disable this search option by setting environment variable `FINDLIBS_DISABLE_CONFIG_PATHS=yes`.

- Next, tries the directories defined by the `$LD_LIBRARY_PATH` and `$DYLD_LIBRARY_PATH` environment variables. Disable this search option by setting environment variable `FINDLIBS_DISABLE_LD_PATH=yes`.

- Next, tries the `lib` and `lib64` directories under the following paths "/", "/usr/", "/usr/local/", "/opt/", "/opt/homebrew/" and "~/.local/". Disable this search option by setting environment variable `FINDLIBS_DISABLE_SYS=yes`.

- Finally, tries calling the `ctypes.util.find_library` function. Disable this search option by setting environment variable `FINDLIBS_DISABLE_CTYPES_UTIL=yes`.