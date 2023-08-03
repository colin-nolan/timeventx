#!/usr/bin/env python3

import sys

from garden_water.configuration import DEFAULT_CONFIGURATION_FILE_NAME, Configuration

config_directory = sys.argv[1]

Configuration.write_env_to_config_file(f"{config_directory}/{DEFAULT_CONFIGURATION_FILE_NAME}")
