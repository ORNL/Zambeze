from __future__ import annotations

import pkgutil
import service_modules.default

from importlib import import_module
from inspect import isclass
from pathlib import Path

class Services:
    def __init__(self):
        """When initialized this class will load all of the services
        located in the service_modules folder"""
        self.__registerServices()

    def __registerServices(self):
        self._services = {}
        service_path = [str(Path(__file__).resolve().parent) + "/service_modules"]
        for importer, module_name, ispkg in pkgutil.walk_packages(path=service_path):
            module = import_module(f"service_modules.{module_name}")
            for attribute_name in dir(module):
                potential_service = getattr(module, attribute_name)
                if isclass(potential_service) and \
                issubclass(potential_service, service_modules.service.Service) and \
                attribute_name != "Service":
                    self._services[attribute_name.lower()] = potential_service()

    @property
    def list(self):
        """List all services that have been registered"""
        services = []
        for key in self._services:
            services.append(key)
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
                self._services[key].configure(config[key]) 
        else:
            for service in services:
                self._services[key].configure(config[key]) 

    def run(self, packages: dict, services: list[str] = ["all"]):
        # We is were magic happens, and all the plugins are going to be printed
        if "all" in services:
            for key in self._services:
                if key in packages:
                    "If a package was passed to be processed"
                    self._services[key].process(packages[key])
                else:
                    "else send an empty package"
                    self._services[key].process({})
        else:
            for service in services:
                if service in packages:
                    self._services[service.lower()].process(packages[service])
                else:
                    self._services[service.lower()].process({})