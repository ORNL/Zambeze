# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

from __future__ import annotations

from .message.abstract_message import AbstractMessage
from .plugin_modules.abstract_plugin import Plugin
from .plugin_modules.common_plugin_functions import registerPlugins
from zambeze.campaign.activities.shell import ShellActivity
from zambeze.campaign.activities.activity import Activity

from copy import deepcopy
from dataclasses import asdict
from importlib import import_module
from inspect import isclass
from typing import Optional, overload

import logging


class PluginChecks(dict):
    def __init__(self, val: dict):
        super().__init__(val)

    def error_detected(self) -> bool:
        """Detects if an error was found in the results of the plugin checks"""
        for key in self.keys():
            for item in self[key]:
                for key2 in item.keys():
                    if item[key2][0] is False:
                        return True
        return False


class Plugins:
    """Plugins class takes care of managing all plugins.

    Plugins can be added as plugins by creating packages in the plugin_modules

    Parameters
    ----------
    logger
        The logger where to log information/warning or errors.
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Constructor

        :param logger: Logger to use, defaults to None
        :type logger: Optional[logging.Logger]
        """
        self.__logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.__module_names = registerPlugins()
        self._plugins = {}

    @property
    def registered(self) -> list[str]:
        """List all plugins that have been registered.

        This method can be called at any time and is meant to simply display
        which packages are supported and present in the plugin_modules
        folder. It does not mean that these plugins have been configured. All
        plugins must be configured before they can be run.

        Returns
        -------
        list of str
            The names of all the plugins that have been registered.
        """
        plugins: list[str] = []
        for module_name in self.__module_names:
            plugins.append(deepcopy(module_name))
        return plugins

    def configure(self, config: dict):
        """
        Configuration options for each plugin

        This method is responsible for initializing all the plugins that are
        supported in the plugin_modules folder. It should be called before
        the plugins can be run, all plugins should be configured before they
        can be run.

        Parameters
        ----------
        config : dict
            This contains relevant configuration information for each plugin,
            if provided will only configure the plugins listed

        Example
        -------
        The configuration options for each plugin will appear under their name
        in the configuration parameter, i.e. for plugins 'globus' and 'shell'.

        >>> config = {
        ...     'globus': {
        ...         'authentication flow': {
        ...             'type': 'credential flow',
        ...             'secret': "blahblah"
        ...         },
        ...         'shell': {
        ...             'arguments' : ['']
        ...         }
        ...     }
        ... }

        >>> plugins = Plugins()
        >>> plugins.configure(config, ['shell'])

        This will just configure the "shell" plugin.
        """
        for module_name in self.__module_names:
            # Registering plugins
            if module_name in config.keys() and module_name in self.__module_names:
                module = import_module(
                    f"zambeze.orchestration.plugin_modules.{module_name}.{module_name}"
                )
                for attribute_name in dir(module):
                    potential_plugin = getattr(module, attribute_name)
                    if isclass(potential_plugin):
                        if (
                            issubclass(potential_plugin, Plugin)
                            and attribute_name != "Plugin"
                        ):
                            self._plugins[attribute_name.lower()] = potential_plugin(
                                logger=self.__logger
                            )

                obj = self._plugins.get(module_name)
                obj.configure(config[module_name])

    @property
    def configured(self) -> list[str]:
        """Will return a list of all the plugins that have been configured.

        Returns
        -------
        list of str
            List of all plugins that are ready to be run.

        Examples
        --------
        If nothing has been configured

        >>> plugins = Plugins()
        >>> assert len(plugins.configured) == 0

        If globus is configured

        >>> config = {
        ...     "globus": {
        ...         "client id": "..."
        ...     }
        ... }

        >>> plugins.configure(config)
        >>> assert len(plugins.configured) == 1
        >>> assert "globus" in plugins.configured
        """
        configured_plugins: list[str] = []
        for key in self._plugins:
            obj = self._plugins.get(key)
            if obj.configured:
                configured_plugins.append(obj.name)

        return configured_plugins

    @property
    def info(self, plugins: list[str] = ["all"]) -> dict:
        """Will return the current state of the registered plugins.

        Parameters
        ----------
        plugins : list of str
            The plugins to provide information about defaults to information
            about all plugins

        Returns
        -------
        dict
            The actual information of each plugin that was specified.

        Example
        -------
        >>> these_plugins = ["globus", "shell"]
        >>> plugins.configure(configuration_options)
        >>> information = plugins.info(these_plugins)
        >>> print(information)
        {
            "globus": {...}
            "shell": {...}
        }
        """
        info = {}
        if "all" in plugins:
            for plugin_inst in self._plugins.keys():
                info[plugin_inst] = self._plugins[plugin_inst].info
        else:
            for plugin_inst in plugins:
                info[plugin_inst] = self._plugins[plugin_inst].info
        return info

    def check(self, msg: Activity, arguments: list = []) -> PluginChecks:
        """Check that the arguments passed to the plugin "plugin_name" are valid

        Parameters
        ----------
        msg : Activity
            Name of the plugin to validate against.
        arguments : dict
            The arguments to be validated for plugin "plugin_name".

        Returns
        -------
        PluginChecks
            What is returned are a list of the plugins and their actions along
            with an indication on whether there was a problem with them.
        """
        if isinstance(msg, ShellActivity):
            arguments = {"arguments": msg.arguments, "command": msg.command}
            plugin_name = "shell"
        else:
            error_msg = "plugin check only currently supports actvities"
            error_msg += " PLUGIN and SHELL, but the following "
            error_msg += "unsupported activity has been specified: "
            error_msg += f"{msg.data.body.type}"
            raise Exception(error_msg)

        if not isinstance(plugin_name, str):
            raise ValueError(
                "[plugins.py] Unsupported plugin_name type detected in check."
                "The check function only supports either:\n"
                "1. An abstract message as a single argument\n"
                "2. The plugin name as a str and the package as a dict\n"
                "\n"
                f"The encountered type is {type(plugin_name)} with payload {plugin_name}"
            )
        elif not isinstance(arguments, dict):
            raise ValueError(
                "[plugins.py] Unsupported arguments type detected in check."
                "The check function only supports either:\n"
                "1. An abstract message as a single argument\n"
                "2. The plugin name as a str and the package as a dict\n"
                "\n"
                f"The encountered type is {type(arguments)} with payload {arguments}"
            )

        check_results = {}

        if plugin_name not in self._plugins.keys():
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
            check_results[plugin_name] = self._plugins[plugin_name].check(arguments)
        return PluginChecks(check_results)

    @overload
    def run(self, msg: AbstractMessage, arguments: Optional[dict] = None) -> None:
        pass

    @overload
    def run(self, msg: str, arguments: dict = {}) -> None:
        pass

    def run(self, msg, arguments=None) -> None:
        """Run a specific plugins.

        Parameters
        ----------
        plugin_name : str
            Plugin name.
        arguments : dict
            Plugin arguments.
        """
        if isinstance(msg, AbstractMessage):
            if msg.type == "PLUGIN":
                arguments = asdict(msg.data.body.parameters)
                plugin_name = msg.data.type
        elif isinstance(msg, ShellActivity):
            if msg.type == "SHELL":
                arguments = {msg.plugin_args["shell"]: msg.plugin_args["parameters"]}
                plugin_name = msg.type
                self.__logger.info("GOODLY")
            else:
                raise Exception(
                    "plugin check only currently supports PLUGIN and SHELL activities"
                )
        else:
            plugin_name = msg

        if not isinstance(plugin_name, str):
            raise ValueError("Unsupported plugin_name type detected in check.")
        if not isinstance(arguments, dict):
            raise ValueError("Unsupported arguments type detected in check.")

        self.__logger.info("GOODLY-2")
        self.__logger.info(plugin_name)
        self._plugins[plugin_name.lower()].process([arguments])
        self.__logger.info("GOODLY-3")
