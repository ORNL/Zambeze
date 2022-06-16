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
        self.logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.__load_settings()
        self.plugins = Plugins(logger=self.logger)

    def __load_settings(self, conf_file: pathlib.Path = None) -> None:
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
            self.settings = yaml.safe_load(cf)

        # set default values
        if not self.settings:
            self.settings = {"nats": {}, "services": {}}
        self.__set_default("host", "localhost", self.settings["nats"])
        self.__set_default("port", 4222, self.settings["nats"])
        self.__set_default("services", {}, self.settings)
        self.__save()

    def get_nats_connection_uri(self) -> str:
        """
        Get the NATS connection URI.

        :return: NATS connection URI
        :rtype: str
        """
        return f"nats://{self.settings['nats']['host']}:{self.settings['nats']['port']}"

    def get_service_names(self) -> list[str]:
        """
        Get a list of service names.

        :return: List of service names
        :rtype: List[str]
        """
        services = []
        for service in self.settings["services"]:
            services.append(service["name"].lower())

    def get_service_properties(
        self, service_name: str
    ) -> dict[str, Union[str, int, float, list]]:
        """
        Get a List of properties from a service.

        :param service_name: Service name
        :type service_name: str

        :return: List of properties
        :rtype: Dict[str, Union[str, int, float, List]]
        """
        for service in self.settings["services"]:
            if service["name"] == service_name:
                return service["properties"]
        return None

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
            yaml.dump(self.settings, file)
