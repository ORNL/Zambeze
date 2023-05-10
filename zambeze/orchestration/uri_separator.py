# Local imports
from .plugin_modules.file_uri_separator import FileURISeparator
from .plugin_modules.common_plugin_functions import registerPlugins
from .plugin_modules.abstract_uri_separator import AbstractURISeparator
from zambeze.log_manager import LogManager

# Standard imports
import logging
from typing import Optional
from urllib.parse import urlparse
from inspect import isclass
import importlib
from importlib import import_module


class URISeparator:
    def __init__(self, logger: LogManager):
        self.__logger: LogManager = logger
        self._uri_separators = {"file": FileURISeparator(logger)}
        self.__module_names = registerPlugins(logger)
        self.__registerURISeparators()

    def __registerURISeparators(self) -> None:
        for module_name in self.__module_names:
            # Registering plugin message validators
            file_and_module = "zambeze.orchestration.plugin_modules."
            file_and_module += f"{module_name}.{module_name}_uri_separator"

            if importlib.util.find_spec(file_and_module):
                print(f"Found {file_and_module}")
                module = import_module(file_and_module)
                for attribute_name in dir(module):
                    potential_plugin_uri_separator = getattr(module, attribute_name)
                    if isclass(potential_plugin_uri_separator):
                        if (
                            issubclass(
                                potential_plugin_uri_separator, AbstractURISeparator
                            )
                            and attribute_name != "AbstractURISeparator"
                        ):
                            print(
                                " - Registering uri separator:"
                                f" {attribute_name.lower()}"
                            )
                            plugin_name = attribute_name.lower().replace(
                                "uriseparator", ""
                            )
                            self._uri_separators[
                                plugin_name
                            ] = potential_plugin_uri_separator(logger=self.__logger)

    def separate(self, uri: str, extra_args=None) -> dict:
        uri_components = urlparse(uri)

        if uri_components.scheme in self._uri_separators.keys():
            return self._uri_separators[uri_components.scheme].separate(uri, extra_args)
        else:
            error_msg = f"Unsupported uri encountered {uri_components.scheme}"
            error_msg += " supported uri types are "
            error_msg += "{self._uri_separators.keys()}"
            raise Exception(error_msg)
