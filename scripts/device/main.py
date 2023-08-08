import sys

libraries_location = "/libs"
sys.path.extend((f"{libraries_location}/packaged", f"{libraries_location}/stdlib"))

from garden_water.main import main

main()
