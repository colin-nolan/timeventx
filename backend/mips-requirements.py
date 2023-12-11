import argparse
import os
from typing import Callable, Optional

import mip


class Library:
    def __init__(
        self,
        name: str,
        mips_kwargs: Optional[dict] = None,
        modifier: Optional[Callable[[str, str, dict], None]] = None,
        package: Optional[str] = None,
    ) -> None:
        self.name = name
        self.mips_kwargs = mips_kwargs
        self.modifier = modifier
        self.package = package


LIBRARIES_TO_INSTALL = (
    # pfalcon's abc package has a couple more dummy definitions than that in micropython-lib
    "github:pfalcon/pycopy-lib/abc/abc.py",
    Library(
        "github:colin-nolan/micropython-lib/micropython/ucontextlib-async/ucontextlib/_async.py",
        dict(version="async_contextlib"),
        lambda source, target_directory, mips_kwargs: os.rename(
            f"{target_directory}/_async.py", f"{target_directory}/ucontentlib_async.py"
        ),
    ),
    "collections",
    # pfalcon's defaultdict package has a couple more definitions than that in micropython-lib to get data out of the defaultdict
    Library("github:pfalcon/pycopy-lib/collections.defaultdict/collections/defaultdict.py", package="collections"),
    "contextlib",
    Library(
        # Fork of PR against micropython-lib to add `configparser` module:
        # https://github.com/micropython/micropython-lib/pull/265
        "github:colin-nolan/micropython-lib/configparser/ConfigParser.py",
        dict(version="mika64-master"),
        lambda source, target_directory, mips_kwargs: os.rename(
            f"{target_directory}/ConfigParser.py", f"{target_directory}/configparser.py"
        ),
    ),
    "datetime",
    "functools",
    "github:pfalcon/pycopy-lib/ffilib/ffilib.py",
    "itertools",
    Library(
        "github:colin-nolan/micropython-lib/python-stdlib/logging/logging.py",
        dict(version="fix/minor-logging-issues"),
    ),
    "os-path",
    "pathlib",
    "time",
    Library("github:colin-nolan/pycopy-lib/typing/typing.py", dict(version="more-types")),
)


def _install_libs(libraries: tuple[str | Library, ...], install_location: str):
    for library in libraries:
        if not isinstance(library, Library):
            assert isinstance(library, str)
            library = Library(library)

        mip_kwargs = dict(target=install_location, mpy=False, **(library.mips_kwargs if library.mips_kwargs else {}))
        if library.package is not None:
            library_install_location = f"{install_location}/{library.package}"
            try:
                os.stat(library_install_location)
            except OSError:
                os.mkdir(library_install_location)
                with open(f"{library_install_location}/__init__.py", "w"):
                    pass
            mip_kwargs["target"] = library_install_location

        mip.install(library.name, **mip_kwargs)

        if library.modifier is not None:
            library.modifier(library.name, mip_kwargs["target"], mip_kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("install_location", help="The location where the libs will be installed")

    args = parser.parse_args()
    install_location = args.install_location
    _install_libs(LIBRARIES_TO_INSTALL, install_location)


if __name__ == "__main__":
    main()
