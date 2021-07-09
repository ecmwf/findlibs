# findlibs

A Python package to search for shared libraries on various platforms.

## Install

```sh
pip install findlibs
```

## Usage

```python
import findlibs
lib = findlibs.find("eccodes")

# If package name is different than the library name
lib = findlibs.find("odccore", "odc")
```

## Development

### Setup Environment

```sh
pip install -r requirements.txt
```

### Run Tests

```sh
python -m pytest
```
