#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import pathlib
import yaml

from typing import Optional, Union
from .orchestration.plugins import Plugins


class ZambezeSettings:
    """
    Zambeze Settings

    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.__logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.load_settings()

    def load_settings(self, conf_file: pathlib.Path = None) -> None:
        """
        Load Zambeze's agent settings

        :param conf_file: Path to configuration file
        :type conf_file: pathlib.Path
        """
        if not conf_file:
            zambeze_folder = pathlib.Path.home().joinpath(".zambeze")
            zambeze_folder.mkdir(parents=True, exist_ok=True)
            self.conf_file = zambeze_folder.joinpath("agent.yaml")
            self.conf_file.touch()

        with open(self.conf_file, "r") as cf:
            self.__settings = yaml.safe_load(cf)

        # set default values
        if not self.__settings:
            self.__settings = {"nats": {}, "plugins": {}}
        self.__set_default("host", "localhost", self.__settings["nats"])
        self.__set_default("port", 4222, self.__settings["nats"])
        self.__set_default("plugins", {}, self.__settings)
        self.__save()

        self.__configure_plugins()

    def __configure_plugins(self) -> None:
        """
        Load and configure Zambeze plugins.
        """
        self.__plugins = Plugins(logger=self.__logger)
        config = {}

        for plugin_name in self.__plugins.registered:
            if plugin_name in self.__settings["plugins"]:
                config[plugin_name] = self.__settings["plugins"][plugin_name]["config"]

        self.__plugins.configure(
            config=config, plugins=list(self.__settings["plugins"].keys())
        )

    def get_nats_connection_uri(self) -> str:
        """
        Get the NATS connection URI.

        :return: NATS connection URI
        :rtype: str
        """
        host = self.__settings["nats"]["host"]
        port = self.__settings["nats"]["port"]
        return f"nats://{host}:{port}"

    def is_plugin_configured(self, plugin_name: str) -> bool:
        """
        Check whether a plugin has been configured.

        :param plugin_name: Plugin name
        :rtype plugin_name: str

        :return: True if the plugin has been configured.
        :rtype: bool
        """
        return plugin_name in self.__plugins.configured

    def run_plugin(self, plugin_name: str, arguments: dict) -> None:
        """

        :param plugin_name:
        :rtype plugin_name: str
        :param arguments:
        :type arguments: dict
        """
        return self.__plugins.run(plugin_name=plugin_name, arguments=arguments)

    def __set_default(
        self, key: str, value: Union[int, float, str, dict], base: dict
    ) -> None:
        """
        Set default setting values.

        :param key: A setting key
        :type key: str
        :param value: The value for the key
        :type value: Union[int, float, str, dict]
        :param base: The dictionary to search for the key
        :type base: dict
        """
        if key not in base:
            base[key] = value

    def __save(self) -> None:
        """
        Save properties file.
        """
        with open(self.conf_file, "w") as file:
            yaml.dump(self.__settings, file)
