import argparse

import mip

LIBRARIES_TO_INSTALL = (
    "abc",
    "collections-defaultdict",
    "datetime",
    "functools",
    "logging",
    "threading",
    "github:pfalcon/pycopy-lib/typing/typing.py",
    # Required by microwebsrv2
    # "github:pfalcon/pycopy-lib/ffilib/ffilib.py",
    # "github:pfalcon/pycopy-lib/select/select.py",
    # "github:pfalcon/pycopy-lib/socket/socket.py",
)


def _install_libs(install_args: tuple[str | tuple[str, dict], ...], install_location: str):
    for args in install_args:
        kwargs = dict(target=install_location, mpy=False)
        if isinstance(args, dict):
            kwargs = args[1] | kwargs
            args = args[0]

        mip.install(args, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("install_location", help="The location where the libs will be installed")

    args = parser.parse_args()
    install_location = args.install_location
    _install_libs(LIBRARIES_TO_INSTALL, install_location)


if __name__ == "__main__":
    main()
