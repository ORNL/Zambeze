# Zambeze internal imports
from .plugin_modules.common_plugin_functions import registerPlugins
from .plugin_modules.abstract_plugin_message_validator import (
    PluginMessageValidator
)

# Standard imports
from importlib import import_module
from inspect import isclass
from typing import Optional

import logging


class PluginsMessageValidator:

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:

        self.__module_names = registerPlugins()
        self._plugin_message_validators = {}

        # self.__registerPlugins()
        self.__registerPluginHelpers()

    def __registerPluginHelpers(self) -> None:
        for module_name in self.__module_names:
            # Registering plugin message validators
            module = import_module(
                "zambeze.orchestration.plugin_modules."
                f"{module_name}.{module_name}_message_helper"
            )
            for attribute_name in dir(module):
                potential_plugin_message_validator = getattr(module, attribute_name)
                if isclass(potential_plugin_message_validator):
                    if (
                        issubclass(
                            potential_plugin_message_validator,
                            PluginMessageValidator)
                        and attribute_name != "PluginMessageValidator"
                    ):
                        print(
                            " - Registering plugin helper:" f" {attribute_name.lower()}"
                        )
                        plugin_name = attribute_name.lower().replace(
                            "messagehelper", ""
                        )
                        self._plugin_message_validators[
                            plugin_name
                        ] = potential_plugin_message_validator(logger=self.__logger)

    def validate(self, plugin_name: str, arguments: dict) -> dict:
        """Check that the arguments passed to the plugin "plugin_name" are valid

        :parameter plugin_name: the name of the plugin to validate against
        :type plugin_name: str
        :parameter arguments: the arguments to be validated for plugin "plugin_name"
        :type arguments: dict
        :return: What is returned are a list of the plugins and their actions
            along with an indication on whether there was a problem with them

        :Example: Using rsync

        For the rsync plugin to be useful, both the local and remote host
        ssh keys must have been configured. By default the rsync plugin will
        look for the private key located at ~/.ssh/id_rsa. If the private key
        is different then it must be specified with the "private_ssh_key" key
        value pair.

        >>> plugins = Plugins()
        >>> config = {
        >>>     "rsync": {
        >>>         "private_ssh_key": "path to private ssh key"
        >>>     }
        >>> }
        >>> plugins.configure(config)
        >>> arguments = {
        >>>     "transfer": {
        >>>         "source": {
        >>>             "ip": local_ip,
        >>>             "user": current_user,
        >>>             "path": current_valid_path,
        >>>         },
        >>>         "destination": {
        >>>             "ip": "172.22.1.69",
        >>>             "user": "cades",
        >>>             "path": "/home/cades/josh-testing",
        >>>         },
        >>>         "arguments": ["-a"],
        >>>     }
        >>> }
        >>> checked_args = plugins.check("rsync", arguments)
        >>> print(checked_args)
        >>> # Should print
        >>> # {
        >>> #   "rsync": { "transfer": True }
        >>> # {
        """
        check_results = {}
        if plugin_name not in self._plugin_message_validators.keys():
            check_results[plugin_name] = [
                {"configured": (False, f"{plugin_name} is not configured.")}
            ]
            if plugin_name not in self.__module_names:
                known_module_names = " ".join(str(mod) for mod in self.__module_names)
                check_results[plugin_name].append(
                    {
                        "registered": (
                            False,
                            f"{plugin_name} is not a known module. "
                            + f"Known modules are: {known_module_names}",
                        )
                    }
                )
        else:
            check_results[plugin_name] = self._plugin_message_validators[
                plugin_name
            ].validateMessage([arguments])
        return check_results
