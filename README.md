# findlibs

A Python package that search for shared libraries on various platforms.

```python
import findlibs
lib = findlibs.find("eccodes")

# If package name differs from library name use:
lib = findlibs.find(lib_name="odccore", pkg_name="odc")
```
