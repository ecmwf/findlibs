import os

import pytest

import findlibs

EXTENSIONS = {
    "linux": ".so",
    "darwin": ".dylib",
    "win32": ".dll",
}


@pytest.mark.parametrize("platform", dict.keys(EXTENSIONS))
@pytest.mark.parametrize("env", ("HOME", "DIR"))
@pytest.mark.parametrize("lib", ("lib", "lib64"))
@pytest.mark.parametrize("found", (True, False))
def test_find_envs(mocker, platform, env, lib, found):
    """
    Checks for correct return value when relying on environment variables.

    Following environment variables will be checked:
    - <libname>_HOME or <LIBNAME>_HOME
    - <libname>_DIR or <LIBNAME>_DIR
    """

    libname = "somename"
    libpath = "/some/path"

    def mock_path_exists(path):
        """Mocks skipping missing lib paths on different parameters"""
        if lib not in path:
            return False
        return found

    for libname_cased in (libname.upper(), libname.lower()):
        mocker.patch("sys.platform", platform)
        mocker.patch(
            "os.environ", {"{}_{}".format(libname_cased, env): libpath}
        )
        mocker.patch("os.path.exists", mock_path_exists)

        result = findlibs.find(libname)
        if found:
            assert result == os.path.join(
                libpath, lib, "lib{}{}".format(libname, EXTENSIONS[platform])
            )
        else:
            assert result is None


@pytest.mark.parametrize("platform", dict.keys(EXTENSIONS))
@pytest.mark.parametrize("env", ("HOME", "DIR"))
@pytest.mark.parametrize("lib", ("lib", "lib64"))
@pytest.mark.parametrize("found", (True, False))
def test_find_envs_pkgname(mocker, platform, env, lib, found):
    """
    Checks for correct return value when relying on environment variables,
    with an optional package name.

    If a package name is passed, it will be used for checking following
    environment variables:
    - <pkgname>_HOME or <PKGNAME>_HOME
    - <pkgname>_DIR or <PKGNAME>_DIR
    """

    libname = "somename"
    pkgname = "differentname"
    libpath = "/some/path"

    def mock_path_exists(path):
        """Mocks skipping missing lib paths on different parameters"""
        if lib not in path:
            return False
        return found

    for pkgname_cased in (pkgname.upper(), pkgname.lower()):
        mocker.patch("sys.platform", platform)
        mocker.patch(
            "os.environ", {"{}_{}".format(pkgname_cased, env): libpath}
        )
        mocker.patch("os.path.exists", mock_path_exists)

        result = findlibs.find(libname, pkgname)
        if found:
            assert result == os.path.join(
                libpath, lib, "lib{}{}".format(libname, EXTENSIONS[platform])
            )
        else:
            assert result is None


@pytest.mark.parametrize("platform", dict.keys(EXTENSIONS))
@pytest.mark.parametrize("env", ("LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH"))
@pytest.mark.parametrize("lib", ("lib", "lib64"))
@pytest.mark.parametrize("found", (True, False))
def test_find_ld_path(mocker, platform, env, lib, found):
    """
    Checks for correct return value when relying on LD paths.

    Following environment variables will be checked:
    - LD_LIBRARY_PATH
    - DYLD_LIBRARY_PATH

    If they contain multiple paths, they will be split on ":" and each
    component will be considered (left to right).
    """

    libname = "somename"
    ld_path = "/some/path/lib:/another/path/lib64"
    ld_paths = {
        "lib": ld_path.split(":")[0],
        "lib64": ld_path.split(":")[1],
    }

    def mock_path_exists(path):
        """Mocks skipping missing lib paths on different parameters"""
        if path == "lib{}{}".format(libname, EXTENSIONS[platform]):
            return False
        if lib not in path:
            return False
        return found

    mocker.patch("sys.platform", platform)
    mocker.patch.dict("os.environ", {env: ld_path})
    mocker.patch("os.path.exists", mock_path_exists)

    result = findlibs.find(libname)
    if found:
        assert result == os.path.join(
            ld_paths[lib], "lib{}{}".format(libname, EXTENSIONS[platform])
        )
    else:
        assert result is None


@pytest.mark.parametrize("platform", dict.keys(EXTENSIONS))
@pytest.mark.parametrize("root", ("/", "/usr/", "/usr/local/", "/opt/"))
@pytest.mark.parametrize("lib", ("lib", "lib64"))
@pytest.mark.parametrize("found", (True, False))
def test_find_common_path(mocker, platform, root, lib, found):
    """
    Checks for correct return value when relying on common paths.

    Following system paths will be checked:
    - /
    - /usr/
    - /usr/local/
    - /opt/
    """

    libname = "somename"

    def mock_path_exists(path):
        """Mocks skipping missing lib paths on different parameters"""
        if root not in path:
            return False
        if lib not in path:
            return False
        return found

    mocker.patch("sys.platform", platform)
    mocker.patch("os.path.exists", mock_path_exists)

    result = findlibs.find(libname)
    if found:
        assert result == os.path.join(
            root, lib, "lib{}{}".format(libname, EXTENSIONS[platform])
        )
    else:
        assert result is None
