#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import os
import pathlib
import yaml
from typing import Optional, Union

from .config import HOST, ZMQ_PORT, NATS_HOST, NATS_PORT
from .orchestration.plugins import Plugins

from zambeze.orchestration.db.dao import create_local_db


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
        # set default values
        self.settings = {"nats": {}, "zmq": {}, "plugins": {}}
        print(self.settings)
        print(self.settings["zmq"])
        self.load_settings(conf_file)

    def load_settings(self, conf_file: Optional[pathlib.Path] = None) -> None:
        """
        Load Zambeze's agent settings

        :param conf_file: Path to configuration file
        :type conf_file: Optional[pathlib.Path]
        """
        self._conf_file = pathlib.Path(conf_file)

        zambeze_folder = pathlib.Path.home().joinpath(".zambeze")
        if not zambeze_folder.exists():
            zambeze_folder.mkdir(parents=True, exist_ok=True)

        default_conf = zambeze_folder.joinpath("agent.yaml")
        if pathlib.Path(self._conf_file) == pathlib.Path(default_conf):
            if not self._conf_file.exists():
                self._conf_file.touch()
                default_settings = {
                    "nats": {"host": NATS_HOST, "port": NATS_PORT},
                    "plugins": {
                        "shell": {"config": {}},
                        "All": {"default_working_directory": os.path.expanduser("~")},
                    },
                    "zmq": {"host": HOST, "port": ZMQ_PORT},
                }
                with open(self._conf_file, "w") as f:
                    yaml.dump(default_settings, f)

        # if not self.settings:
        #    self.settings = {"nats": {}, "zmq": {}, "plugins": {}}

        self._logger.info(f"Loading settings from config file: {self._conf_file}")
        with open(self._conf_file, "r") as cf:
            self.settings.update(yaml.safe_load(cf))

        # Ideally the plugin modules would have the default settings located
        # in their files and they could just be asked here.
        self.__set_default("host", NATS_HOST, self.settings["nats"])
        self.__set_default("port", NATS_PORT, self.settings["nats"])
        self.__set_default("host", HOST, self.settings["zmq"])
        self.__set_default("port", ZMQ_PORT, self.settings["zmq"])
        self.__set_default("plugins", {"All": {}}, self.settings)
        self.__set_default("All", {}, self.settings["plugins"])
        self.__set_default(
            "default_working_directory",
            os.path.expanduser("~"),
            self.settings["plugins"]["All"],
        )
        self.__save()

        create_local_db()

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

    #    def get_nats_connection_uri(self) -> str:
    #        """
    #        Get the NATS connection URI.
    #
    #        :return: NATS connection URI
    #        :rtype: str
    #        """
    #        host = self.settings["nats"]["host"]
    #        port = self.settings["nats"]["port"]
    #        return f"nats://{host}:{port}"

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
