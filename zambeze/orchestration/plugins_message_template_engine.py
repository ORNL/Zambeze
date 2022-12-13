# Zambeze internal imports
from .plugin_modules.common_plugin_functions import registerPlugins
from .plugin_modules.abstract_plugin_template_generator import (
    PluginMessageTemplateGenerator,
)

# Standard imports
from importlib import import_module
from inspect import isclass
from typing import Optional

import logging


class PluginsMessageTemplateEngine:
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.__logger = logger
        if self.__logger is None:
            self.__logger = logging.Logger()

        self.__module_names = registerPlugins()
        self._plugin_message_template_generators = {}
        self.__registerPluginTemplateGenerators()

    def __registerPluginTemplateGenerators(self) -> None:
        print(self.__module_names)
        for module_name in self.__module_names:
            # Registering plugin message validators
            print(module_name)
            module = import_module(
                "zambeze.orchestration.plugin_modules."
                f"{module_name}.{module_name}_message_template_generator"
            )
            for attribute_name in dir(module):
                potential_plugin_message_template_generator = getattr(
                    module, attribute_name
                )
                if isclass(potential_plugin_message_template_generator):
                    if (
                        issubclass(
                            potential_plugin_message_template_generator,
                            PluginMessageTemplateGenerator,
                        )
                        and attribute_name != "PluginMessageTemplateGenerator"
                    ):
                        print(
                            " - Registering plugin template generator:"
                            f" {attribute_name.lower()}"
                        )
                        print(f"Attribute nameis {attribute_name}")
                        plugin_name = attribute_name.lower().replace(
                            "messagetemplategenerator", ""
                        )
                        self._plugin_message_template_generators[
                            plugin_name
                        ] = potential_plugin_message_template_generator(
                            logger=self.__logger
                        )

    def generate(self, plugin_name: str, args):
        """Will return a template of the message body this can be used by the
        message factory to convert it into an Abstract Message which can be
        processed by the run and or check commands.
        """

        message_template = self._plugin_message_template_generators[
            plugin_name
        ].generate(args)
        message_template.plugin = plugin_name
        return message_template
