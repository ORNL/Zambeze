from __future__ import annotations

import pkgutil
from .service_modules import default
from .service_modules import service
from copy import deepcopy
from importlib import import_module
from inspect import isclass
from pathlib import Path
from types import ModuleType

class Services:
    def __init__(self):
        """When initialized this class will load all of the services
        located in the service_modules folder"""
        self.__registerServices()

    def __registerServices(self):
        self._services = {}

        service_path = [str(Path(__file__).resolve().parent) + "/service_modules"]
        for importer, module_name, ispkg in pkgutil.walk_packages(path=service_path):
            module = import_module(f"zambeze.orchestrator.service_modules.{module_name}")
            for attribute_name in dir(module):
                potential_service = getattr(module, attribute_name)
                if isclass(potential_service):
                    if issubclass(potential_service, service.Service) and \
                    attribute_name != "Service":
                        self._services[attribute_name.lower()] = potential_service()

    def registered(self) -> list:
        """List all services that have been registered"""
        services = []
        for key in self._services:
            print(f"key is {key}")
            services.append(deepcopy(key))
        return services

    def configure(self, config: dict, services: list[str] = ["all"]):
        """Configuration options "config" for each service should be part of
        the dict and appear under a heading associated with the name of the 
        service.

        I.e. for services "globus" and "shell"

        {   "globus": {
                "client id": "..."
            }
            "shell": {
                "arguments" : [""]
            }
        } 
        """
        if "all" in services:
            for key in self._services:
                if key in config.keys():
                    obj = self._services.get(key)
                    obj.configure(config[key]) 
        else:
            for service in services:
                if key in config.keys():
                    self._services[service.lower()].configure(config[service.lower()]) 

    @property
    def info(self, services: list[str] = ["all"]) -> dict:
        """Will return the current state of the services that are registered with their configuration options"""
        info = {}
        if "all" in services:
            for service in self._services.keys():
                info[service] = self._services[service].info
        else:
            for service in services:
                info[service] = self._services[service].info
        return info

    def run(self, packages: dict, services: list[str] = ["all"]):
        # We is were magic happens, and all the plugins are going to be printed
        if "all" in services:
            for key in self._services:
                if key in packages.keys():
                    "If a package was passed to be processed"
                    self._services[key].process(packages[key])
                else:
                    "else send an empty package"
                    self._services[key].process({})
        else:
            for service in services:
                if service in packages.keys():
                    self._services[service.lower()].process(packages[service])
                else:
                    self._services[service.lower()].process({})