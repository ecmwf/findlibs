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

`pip install findlibs`

## Testing

```bash
git clone https://github.com/ecmwf/findlibs
cd findlibs
pip install -e ".[test]"
pytest
```

## find()

The module only contains function `find()`.

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

- First, tries the `lib` and `lib64` directories under `sys.prefix` and `$CONDA_PREFIX`

- Next, tries the `lib` and `lib64` directories under the paths defined by the `pkg_name + "_HOME"` and `pkg_name + "_DIR"` environment variables. Both lowercase and uppercase versions are tested. E.g. if `pkg_name` is "eccodes" it will check the paths defined by `$eccodes_dir`, `$eccodes_home`, `$ECCODES_DIR` and `$ECCODES_HOME`.

- Next, tries to load the search paths from the user defined `~/.findlibs` or `~/.config/findlibs/findlibs.conf` INI configuration files. Then for all the user defined paths the `lib` and `lib64` directories are tried. 

    Please note that only one of these files may exist. The file can contain multiple search paths, but no relative paths or paths to files are allowed. The config file can even be completely empty or can contain no paths at all. For all the the `lib` and `lib64` directories The file format is as follows:

    ```
    [Paths]
    /path/to/lib_directory
    ```

- Next, tries the directories defined by the `$LD_LIBRARY_PATH` and `$DYLD_LIBRARY_PATH` environment variables

- Finally, tries the `lib` and `lib64` directories under the following paths "/", "/usr/", "/usr/local/", "/opt/", "/opt/homebrew/" and "~/.local/"
