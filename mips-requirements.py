# TODO: move to micropython directory
import argparse
import os

import mip

LIBRARIES_TO_INSTALL = (
    "abc",
    "collections-defaultdict",
    "contextlib",
    (
        # PR against micropython-lib to add `configparser` module
        "github:colin-nolan/micropython-lib/configparser/ConfigParser.py",
        dict(version="mika64-master"),
        lambda source, mips_kwargs: os.rename(
            f"{mips_kwargs['target']}/ConfigParser.py", f"{mips_kwargs['target']}/configparser.py"
        ),
    ),
    "datetime",
    "functools",
    "github:pfalcon/pycopy-lib/ffilib/ffilib.py",
    "inspect",
    "itertools",
    (
        "github:colin-nolan/micropython-lib/python-stdlib/logging/logging.py",
        dict(version="fix/minor-logging-issues"),
    ),
    (
        "github:colin-nolan/micropython-lib/micropython/ucontextlib-async/ucontextlib/_async.py",
        dict(version="async_contextlib"),
        lambda source, mips_kwargs: os.rename(
            f"{mips_kwargs['target']}/_async.py", f"{mips_kwargs['target']}/ucontentlib_async.py"
        ),
    ),
    "pathlib",
    "time",
    ("github:colin-nolan/pycopy-lib/typing/typing.py", dict(version="more-types")),
)


def _install_libs(install_args: tuple[str | tuple[str, dict] | tuple[str, dict, callable], ...], install_location: str):
    for args in install_args:
        mip_kwargs = dict(target=install_location, mpy=False)
        if not isinstance(args, tuple):
            source = args
        else:
            mip_kwargs = args[1] | mip_kwargs
            source = args[0]

        mip.install(source, **mip_kwargs)

        if isinstance(args, tuple) and len(args) > 2:
            args[2](source, mip_kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("install_location", help="The location where the libs will be installed")

    args = parser.parse_args()
    install_location = args.install_location
    _install_libs(LIBRARIES_TO_INSTALL, install_location)


if __name__ == "__main__":
    main()
