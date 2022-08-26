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

    :param conf_file: Path to configuration file
    :type conf_file: Optional[pathlib.Path]
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(
        self,
        conf_file: Optional[pathlib.Path] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Zambeze settings."""
        self._logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.load_settings(conf_file)

    def load_settings(self, conf_file: Optional[pathlib.Path] = None) -> None:
        """
        Load Zambeze's agent settings

        :param conf_file: Path to configuration file
        :type conf_file: Optional[pathlib.Path]
        """
        self._conf_file = conf_file
        if not self._conf_file:
            zambeze_folder = pathlib.Path.home().joinpath(".zambeze")
            zambeze_folder.mkdir(parents=True, exist_ok=True)
            self._conf_file = zambeze_folder.joinpath("agent.yaml")
            self._conf_file.touch()

        self._logger.info(f"Loading settings from config file: {self._conf_file}")
        with open(self._conf_file, "r") as cf:
            self.settings = yaml.safe_load(cf)

        # set default values
        if not self.settings:
            self.settings = {"nats": {}, "zmq": {}, "plugins": {}}
        self.__set_default("host", "localhost", self.settings["nats"])
        self.__set_default("port", 4222, self.settings["nats"])
        self.__set_default("port", 5555, self.settings["zmq"])
        self.__set_default("plugins", {}, self.settings)
        self.__save()

        self.__configure_plugins()

    def __configure_plugins(self) -> None:
        """
        Load and configure Zambeze plugins.
        """
        self.plugins = Plugins(logger=self._logger)
        config = {}

        for plugin_name in self.plugins.registered:
            if plugin_name in self.settings["plugins"]:
                self._logger.info(f"Configuring Plugin: {plugin_name}")
                config[plugin_name] = self.settings["plugins"][plugin_name]["config"]

        self.plugins.configure(config=config)

    def get_nats_connection_uri(self) -> str:
        """
        Get the NATS connection URI.

        :return: NATS connection URI
        :rtype: str
        """
        host = self.settings["nats"]["host"]
        port = self.settings["nats"]["port"]
        return f"nats://{host}:{port}"

    def get_zmq_connection_uri(self) -> str:
        """
        Get the ZMQ connection URI.

        :return: ZMQ connection URI
        :rtype: str
        """
        port = self.settings["zmq"]["port"]
        return f"tcp://*:{port}"

    def is_plugin_configured(self, plugin_name: str) -> bool:
        """
        Check whether a plugin has been configured.

        :param plugin_name: Plugin name
        :rtype plugin_name: str

        :return: True if the plugin has been configured.
        :rtype: bool
        """
        return plugin_name in self.plugins.configured

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
        with open(self._conf_file, "w") as file:
            yaml.dump(self.settings, file)
