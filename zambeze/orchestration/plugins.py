#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Required to occur first
from __future__ import annotations

# Local imports
from .plugin_modules.abstract_plugin import Plugin

# Standard imports
from copy import deepcopy
from importlib import import_module
from inspect import isclass
from pathlib import Path
from typing import Optional

import logging
import pkgutil


class Plugins:
    """Plugins class takes care of managing all plugins.

    Plugins can be added as plugins by creating packages in the plugin_modules

    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Constructor"""
        self.__logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.__registerPlugins()

    def __registerPlugins(self) -> None:
        """Will register all the plugins provided in the plugin_modules folder"""
        self._plugins = {}
        module_names = []

        plugin_path = [str(Path(__file__).resolve().parent) + "/plugin_modules"]
        for importer, module_name, ispkg in pkgutil.walk_packages(path=plugin_path):
            module = import_module(
                f"zambeze.orchestration.plugin_modules.{module_name}"
            )
            module_names.append(module_name)
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
        self.__logger.debug(f"Registered Plugins: {', '.join(module_names)}")

    @property
    def registered(self) -> list[Plugin]:
        """List all plugins that have been registered.

        This method can be called at any time and is meant to simply display which
        packages are supported and present in the plugin_modules folder. It does
        not mean that these plugins have been configured. All plugins must be
        configured before they can be run.

        :return: Returns the names of all the plugins that have been registered
        :rtype: list[str]

        Examples
        Plugins plugins

        for plugin_inst in plugins.registered:
            print(plugin)

        >>> globus
        >>> shell
        >>> rsync
        """
        plugins: list[Plugin] = []
        for key in self._plugins:
            plugins.append(deepcopy(key))
        return plugins

    def configure(self, config: dict, plugins: list[str] = ["all"]) -> None:
        """Configuration options for each plugin

        This method is responsible for initializing all the plugins that
        are supported in the plugin_modules folder. It should be called before the
        plugins can be run, all plugins should be configured before they can be
        run.

        :param config: This contains relevant configuration information for each plugin
        :type config: dict
        :param plugins: If provided will only register the plugins listed
        :type plugins: list[str]

        Example Arguments

        The configuration options for each plugin will appear under their name
        in the configuration parameter.

        I.e. for plugins "globus" and "shell"

        config = {
            "globus": {
                "client id": "..."
            },
            "shell": {
                "arguments" : [""]
            }
        }

        plugins = Plugins()

        plugins.configure(config, ["shell"])

        This will just configure the "shell" plugin

        """
        if "all" in plugins:
            for key in self._plugins:
                if key in config.keys():
                    obj = self._plugins.get(key)
                    obj.configure(config[key])
                else:
                    try:
                        obj = self._plugins.get(key)
                        obj.configure({})
                    except Exception:
                        print(
                            f"Unable to configure plugin {key} missing "
                            "configuration options."
                        )
                        raise
        else:
            for plugin_inst in plugins:
                if plugin_inst in config.keys():
                    self._plugins[plugin_inst.lower()].configure(
                        config[plugin_inst.lower()]
                    )
                else:
                    try:
                        obj = self._plugins.get(plugin_inst)
                        obj.configure({})
                    except Exception:
                        print(
                            f"Unable to configure plugin {plugin_inst} "
                            "missing configuration options."
                        )
                        print("Configuration has the following content")
                        print(config)
                        print(
                            f"{plugin_inst} is not mentioned in the config so "
                            "cannot associate configuration settings."
                        )
                        raise

    @property
    def configured(self) -> list[str]:
        """Will return a list of all the plugins that have been configured.

        :return: list of all plugins that are ready to be run
        :rtype: list[str]

        Example: if nothing has been configured

        plugins = Plugins()

        assert len(plugins.configured) == 0

        Example: if globus is configured

        config = {
            "globus": {
                "client id": "..."
            }
        }

        plugins.configure(config)

        assert len(plugins.configured) == 1
        assert "globus" in plugins.configured

        """
        configured_plugins: list[str] = []
        for key in self._plugins:
            obj = self._plugins.get(key)
            if obj.configured:
                configured_plugins.append(obj.name)

        return configured_plugins

    @property
    def info(self, plugins: list[str] = ["all"]) -> dict:
        """Will return the current state of the registered plugins

        :param plugins: the plugins to provide information about
        :default plugins: information about all plugins
        :type plugins: list[str]
        :return: The actual information of each plugin that was specified
        :rtype: dict

        Example Arguments

        plugins = ["globus", "shell"]

        Examples

        Plugins plugins
        plugins.configure(configuration_options)
        information = plugins.info
        print(information)

        >>> {
        >>>    "globus": {...}
        >>>    "shell": {...}
        >>> }
        """
        info = {}
        if "all" in plugins:
            for plugin_inst in self._plugins.keys():
                info[plugin_inst] = self._plugins[plugin_inst].info
        else:
            for plugin_inst in plugins:
                info[plugin_inst] = self._plugins[plugin_inst].info
        return info

    def check(self, plugin_name: str, arguments: dict) -> None:
        """Check that the arguments passed to the plugin "plugin_name" are valid

        :param plugin_name: the name of the plugin to validate against
        :type plugin_name: str
        :param arguments: the arguments to be validated for plugin "plugin_name"
        :type arguments: dict

        Example

        Assuming we are validating that the following arguments are provided for
        the rsync plugin

        plugins = Plugins()

        config = {
            "rsync": {
                "private_ssh_key": "path to private ssh key"
            }
        }
        plugins.configure()

        arguments = {
            "transfer": {
                "source": {
                    "ip": local_ip,
                    "user": current_user,
                    "path": current_valid_path,
                },
                "destination": {
                    "ip": "172.22.1.69",
                    "user": "cades",
                    "path": "/home/cades/josh-testing",
                },
                "arguments": ["-a"],
            }
        }


        """
        check_results = {}
        check_results[plugin_name] = self._plugins[plugin_name].check([arguments])
        return check_results

    def run(self, plugin_name: str, arguments: dict) -> None:
        """Run a specific plugins.

        :param plugin_name: Plugin name
        :type plugin_name: str
        :param arguments: Plugin arguments
        :type arguments: dict

        plugins = Plugins()

        config = {
                "rsync": {
                        "ssh_key": "path to private ssh key"
                }
        }
        plugins.configure(config)

        arguments = {
                "transfer": {
                        "source": {
                                "ip":
                                "hostname":
                                "path":
                        },
                        "destination": {
                                "ip":
                                "hostname":
                                "path":
                        }
                }
        }

        # Should return True for each action that was found to be
        # correctly validated
        checks = plugins.check('rsync', arguments)

        print(checks)

        plugins.run('rsync', arguments)

        >>> {"transfer": True }
        """
        self._plugins[plugin_name].process([arguments])
