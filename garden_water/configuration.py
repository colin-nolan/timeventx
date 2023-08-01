from configparser import ConfigParser
import os
from pathlib import Path
from typing import Optional, Any


ENVIRONMENT_VARIABLE_PREFIX = "GARDEN_WATER"


# Not using dataclass as not supported by MicroPython
class ConfigurationDescription:
    def __init__(self, environment_variable_name: str, ini_name: str, parser: callable, empty_allowed: bool = False):
        self.environment_variable_name = environment_variable_name
        self.ini_name = ini_name
        self.parser = parser
        self.empty_allowed = empty_allowed

    def get_ini_section(self) -> str:
        section = "".join(self.ini_name.split(".")[:-1])
        return section if section != self.ini_name else "DEFAULT"

    def get_ini_option(self) -> str:
        return self.ini_name.split(".")[-1]


class Configuration:
    WIFI_SSID = ConfigurationDescription(f"{ENVIRONMENT_VARIABLE_PREFIX}_WIFI_SSID", "wifi.ssid", str)
    WIFI_PASSWORD = ConfigurationDescription(f"{ENVIRONMENT_VARIABLE_PREFIX}_WIFI_PASSWORD", "wifi.password", str)
    LOG_LEVEL = ConfigurationDescription(f"{ENVIRONMENT_VARIABLE_PREFIX}_LOG_LEVEL", "log.level", int)
    LOG_FILE_LOCATION = ConfigurationDescription(
        f"{ENVIRONMENT_VARIABLE_PREFIX}_LOG_FILE_LOCATION", "log.file_location", str
    )

    @staticmethod
    def write_env_to_config_file(config_file_location: Path):
        """
        Writes environment variables to a configuration file.
        :param config_file_location: the location of the configuration file to write to
        """
        configuration_descriptions = (
            getattr(Configuration, attr_name)
            for attr_name in dir(Configuration)
            if not attr_name.startswith("_")
            and attr_name.isupper()
            and isinstance(getattr(Configuration, attr_name), ConfigurationDescription)
        )
        configuration_parser = ConfigParser()

        for configuration_description in configuration_descriptions:
            value = os.environ.get(configuration_description.environment_variable_name, "")

            if value == "" and not configuration_description.empty_allowed:
                continue

            section = configuration_description.get_ini_section()
            if not configuration_parser.has_section(section):
                configuration_parser.add_section(section)

            # Using subscribable syntax as expected to run on CPython's implementation of `configparser`
            configuration_parser[configuration_description.get_ini_section()][
                configuration_description.get_ini_option()
            ] = value

        with open(config_file_location, "w") as config_file:
            configuration_parser.write(config_file)

    def __init__(self, config_file_location: Optional[Path] = None):
        self._configuration_parser = ConfigParser()
        if config_file_location:
            self._configuration_parser.read(str(config_file_location))

    def __getitem__(self, configuration_description: ConfigurationDescription) -> Any:
        try:
            value = os.environ[configuration_description.environment_variable_name]
        except (KeyError, AttributeError, OSError):
            # Using legacy API `get` opposed to subscribable syntax as expected to run on minimal `configparser`
            # implementation that is compatible with MicroPython
            try:
                value = self._configuration_parser.get(
                    configuration_description.get_ini_section(), configuration_description.get_ini_option()
                )
            except Exception as e:
                raise KeyError(f"Configuration value not found: {configuration_description.ini_name}") from e

        if value == "" and not configuration_description.empty_allowed:
            raise AttributeError(
                f"Configuration value for {configuration_description.environment_variable_name} is empty, which has "
                + f"been set as not allowed"
            )

        return configuration_description.parser(value)

    def get(self, configuration_description: ConfigurationDescription, default: Optional[Any] = None) -> Any:
        try:
            return self[configuration_description]
        except KeyError:
            return default