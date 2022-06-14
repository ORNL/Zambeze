# Required to occur first
from __future__ import annotations

# Local imports
from .plugin_modules import plugin

# Standard imports
from copy import deepcopy
from importlib import import_module
from inspect import isclass
from pathlib import Path

import pkgutil


class Plugins:
    """Plugins class takes care of managing all plugins.

    Plugins can be added as plugins by creating packages in the plugin_modules
    """

    def __init__(self):
        """Constructor"""
        self.__registerPlugins()

    def __registerPlugins(self):
        """Will register all the plugins provided in the plugin_modules folder"""
        self._plugins = {}

        plugin_path = [str(Path(__file__).resolve().parent) + "/plugin_modules"]
        for importer, module_name, ispkg in pkgutil.walk_packages(path=plugin_path):
            module = import_module(
                f"zambeze.orchestration.plugin_modules.{module_name}"
            )
            for attribute_name in dir(module):
                potential_plugin = getattr(module, attribute_name)
                if isclass(potential_plugin):
                    if (
                        issubclass(potential_plugin, plugin.Plugin)
                        and attribute_name != "Plugin"
                    ):
                        self._plugins[attribute_name.lower()] = potential_plugin()

    @property
    def registered(self) -> list:
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
        plugins = []
        for key in self._plugins:
            plugins.append(deepcopy(key))
        return plugins

    def configure(self, config: dict):
        """Configuration options for each plugin

        This method is responsible for initializing all the plugins that
        are supported in the plugin_modules folder. It should be called before the
        plugins can be run, all plugins should be configured before they can be
        run.

        :param config: This contains relevant configuration information for each plugin,
        If provided will only configure the plugins listed
        :type config: dict

        Example Arguments

        The configuration options for each plugin will appear under their name
        in the configuration parameter.

        I.e. for plugins "globus" and "shell"

        {   "globus": {
                "authentication flow": {
                    "type": "credential flow",
                    "secret": "blahblah"

            }
            "shell": {
                "arguments" : [""]
            }
        }


        """
        for key in self._plugins:
            if key in config.keys():
                obj = self._plugins.get(key)
                obj.configure(config[key])

    #                else:
    #                    try:
    #                        obj = self._plugins.get(key)
    #                        obj.configure({})
    #                    except Exception:
    #                        print(
    #                            f"Unable to configure plugin {key} missing "
    #                            "configuration options."
    #                        )
    #                        raise
    #       else:
    #           for plugin_inst in plugins:
    #               if plugin_inst in config.keys():
    #                   self._plugins[plugin_inst.lower()].configure(
    #                       config[plugin_inst.lower()]
    #                   )
    #                else:
    #                    try:
    #                        obj = self._plugins.get(plugin_inst)
    #                        obj.configure({})
    #                    except Exception:
    #                        print(
    #                            f"Unable to configure plugin {plugin_inst} "
    #                            "missing configuration options."
    #                        )
    #                        print("Configuration has the following content")
    #                        print(config)
    #                        print(
    #                            f"{plugin_inst} is not mentioned in the config so "
    #                            "cannot associate configuration settings."
    #                        )
    #                        raise
    #
    @property
    def configured(self) -> list[str]:
        """Will return a list of all the plugins that have been configured.

        :return: list of all plugins that are ready to be run
        :rtype: list[str]
        """
        configured_plugins = []
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

    def check(self, arguments: dict, plugins: list[str] = ["all"]):
        """Run the plugins specified.

        :param arguments: the arguments to provide to each of the plugins that
        are to be run
        :type arguments: dict
        :param plugins: The list of all the plugins to run
        :type plugins: list[str]
        """
        check_results = {}
        if "all" in plugins:
            for key in self._plugins:
                if key in arguments.keys():
                    # If a package was passed to be processed"
                    check_results[key] = self._plugins[key].check(arguments[key])
                else:
                    # else send an empty package"
                    check_results[key] = self._plugins[key].check({})
        else:
            for plugin_inst in plugins:
                if plugin_inst in arguments.keys():
                    check_results[plugin_inst.lower()] = self._plugins[
                        plugin_inst.lower()
                    ].check(arguments[plugin_inst])
                else:
                    check_results[plugin_inst.lower()] = self._plugins[
                        plugin_inst.lower()
                    ].check({})
        return check_results

    def run(self, arguments: dict, plugins: list[str] = ["all"]):
        """Run the plugins specified.

        :param arguments: the arguments to provide to each of the plugins that
        are to be run
        :type arguments: dict
        :param plugins: The list of all the plugins to run
        :type plugins: list[str]
        """
        if "all" in plugins:
            for key in self._plugins:
                if key in arguments.keys():
                    # If a package was passed to be processed"
                    self._plugins[key].process(arguments[key])
                else:
                    # else send an empty package"
                    self._plugins[key].process({})
        else:
            for plugin_inst in plugins:
                if plugin_inst in arguments.keys():
                    self._plugins[plugin_inst.lower()].process(arguments[plugin_inst])
                else:
                    self._plugins[plugin_inst.lower()].process({})
