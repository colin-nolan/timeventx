import sys

_libraries_location = "/libs"
sys.path.extend((f"{_libraries_location}/packaged", f"{_libraries_location}/stdlib"))

from timeventx.main import main

if __name__ == "__main__":
    main()
