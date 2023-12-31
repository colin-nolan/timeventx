import logging
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Any, Iterable, Optional

from timeventx._logging import get_logger

ENVIRONMENT_VARIABLE_PREFIX = "TIMEVENTX"
DEFAULT_CONFIGURATION_FILE_NAME = "config.ini"

logger = get_logger(__name__)


# Not using dataclass as not supported by MicroPython
class ConfigurationDescription:
    @property
    def name(self) -> str:
        return self.ini_name

    @property
    def ini_section(self) -> str:
        section = "".join(self.ini_name.split(".")[:-1])
        return section if section != self.ini_name else "DEFAULT"

    @property
    def ini_option(self) -> str:
        return self.ini_name.split(".")[-1]

    def __init__(
        self,
        environment_variable_name: str,
        ini_name: str,
        deserialiser: callable,
        default: Any = None,
        allow_none: bool = True,
    ):
        self.environment_variable_name = environment_variable_name
        self.ini_name = ini_name
        self.deserialiser = deserialiser
        self.default = default
        self.allow_none = allow_none


class ConfigurationNotFoundError(RuntimeError):
    def __init__(self, configuration_description: ConfigurationDescription):
        hint = (
            f" (can be set set using {configuration_description.environment_variable_name})"
            if hasattr(os, "environ")
            else ""
        )
        super().__init__(f"Configuration not found for: {configuration_description.name}{hint}")
        self.configuration_description = configuration_description


class Configuration:
    LOG_LEVEL = ConfigurationDescription(
        f"{ENVIRONMENT_VARIABLE_PREFIX}_LOG_LEVEL", "log.level", int, default=logging.INFO
    )
    LOG_FILE_LOCATION = ConfigurationDescription(
        f"{ENVIRONMENT_VARIABLE_PREFIX}_LOG_FILE_LOCATION", "log.file_location", Path, default="/main.log"
    )
    TIMERS_DATABASE_LOCATION = ConfigurationDescription(
        f"{ENVIRONMENT_VARIABLE_PREFIX}_TIMERS_DATABASE_LOCATION", "database.location", Path, default="/data/timers"
    )
    WIFI_SSID = ConfigurationDescription(f"{ENVIRONMENT_VARIABLE_PREFIX}_WIFI_SSID", "wifi.ssid", str, allow_none=False)
    WIFI_PASSWORD = ConfigurationDescription(
        f"{ENVIRONMENT_VARIABLE_PREFIX}_WIFI_PASSWORD", "wifi.password", str, allow_none=False
    )
    FRONTEND_ROOT_DIRECTORY = ConfigurationDescription(
        f"{ENVIRONMENT_VARIABLE_PREFIX}_FRONTEND_ROOT_DIRECTORY",
        "frontend.root",
        Path,
        default="/frontend",
    )
    BACKEND_PORT = ConfigurationDescription(
        f"{ENVIRONMENT_VARIABLE_PREFIX}_BACKEND_PORT", "backend.port", int, default=80
    )
    BACKEND_HOST = ConfigurationDescription(
        f"{ENVIRONMENT_VARIABLE_PREFIX}_BACKEND_INTERFACE", "backend.interface", str, default="0.0.0.0"
    )
    RESTART_ON_ERROR = ConfigurationDescription(
        f"{ENVIRONMENT_VARIABLE_PREFIX}_RESTART_ON_ERROR",
        "restart.on_error",
        lambda value: True if value.lower() == "true" else False,
        default=True,
    )
    ACTION_CONTROLLER_MODULE = ConfigurationDescription(
        f"{ENVIRONMENT_VARIABLE_PREFIX}_ACTION_CONTROLLER_MODULE", "actions.module", str, allow_none=False
    )
    # Credentials expected in the form: base64("user:password"),base64("user2:password2")
    BASE64_ENCODED_CREDENTIALS = ConfigurationDescription(
        f"{ENVIRONMENT_VARIABLE_PREFIX}_BASE64_ENCODED_CREDENTIALS",
        "authentication.base64_credentials",
        lambda x: x.split(","),
        default=None,
    )

    @staticmethod
    def get_configuration_descriptions() -> Iterable[ConfigurationDescription]:
        return (
            getattr(Configuration, attr_name)
            for attr_name in dir(Configuration)
            if not attr_name.startswith("_")
            and attr_name.isupper()
            and isinstance(getattr(Configuration, attr_name), ConfigurationDescription)
        )

    @staticmethod
    def write_env_to_config_file(config_file_location: Path):
        """
        Writes environment variables to a configuration file.
        :param config_file_location: the location of the configuration file to write to
        """
        configuration_parser = ConfigParser()

        for configuration_description in Configuration.get_configuration_descriptions():
            value = os.environ.get(configuration_description.environment_variable_name)

            if value is None:
                value = configuration_description.default

                if value is None:
                    if not configuration_description.allow_none:
                        raise ValueError(
                            f"Configuration value must be set for {configuration_description.name} "
                            + f"(could set {configuration_description.environment_variable_name})"
                        )
                    continue
                else:
                    value = str(value)

            section = configuration_description.ini_section
            if not configuration_parser.has_section(section):
                configuration_parser.add_section(section)

            # Using subscribable syntax as expected to run on CPython's implementation of `configparser`
            configuration_parser[configuration_description.ini_section][configuration_description.ini_option] = value

        with open(config_file_location, "w") as config_file:
            configuration_parser.write(config_file)

    def __init__(self, config_file_location: Optional[Path] = None):
        self._config_file_location = config_file_location
        self._configuration_parser = ConfigParser()
        if self._config_file_location:
            self._configuration_parser.read(str(self._config_file_location))

    def __getitem__(self, configuration_description: ConfigurationDescription) -> Any:
        try:
            logger.debug(
                f"Attempting to get configuration value from the environment: "
                + f"{configuration_description.environment_variable_name}"
            )
            value = os.environ[configuration_description.environment_variable_name]
        except (KeyError, AttributeError, OSError):
            try:
                if self._config_file_location is None:
                    raise FileNotFoundError("No configuration file location setup")

                logger.debug(
                    f'Attempting to get configuration value "{configuration_description.ini_name}" from the '
                    + f"file: {self._config_file_location}"
                )
                # Using legacy API `get` opposed to subscribable syntax as expected to run on minimal `configparser`
                # implementation that is compatible with MicroPython
                value = self._configuration_parser.get(
                    configuration_description.ini_section, configuration_description.ini_option
                )
            except Exception as e:
                raise ConfigurationNotFoundError(configuration_description) from e

        parsed_value = configuration_description.deserialiser(value)
        logger.debug(f'Got value for "{configuration_description.ini_name}": {parsed_value}')
        return parsed_value

    def get(self, configuration_description: ConfigurationDescription, default: Optional[Any] = None) -> Any:
        try:
            return self[configuration_description]
        except ConfigurationNotFoundError:
            return default

    def get_with_standard_default(self, configuration_description: ConfigurationDescription) -> Any:
        return self.get(configuration_description, configuration_description.default)
