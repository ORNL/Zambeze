# Required to occur first
from __future__ import annotations

# Local imports
from .service_modules import service

# Standard imports
from copy import deepcopy
from importlib import import_module
from inspect import isclass
from types import ModuleType
from pathlib import Path

import pkgutil


class Services:
    """Services class takes care of managing all services.

    Services can be added as plugins by creating packages in the service_modules
    """

    def __init__(self):
        """Constructor"""
        self.__registerServices()

    def __registerServices(self):
        """Will register all the services provided in the service_modules folder"""
        self._services = {}

        service_path = [str(Path(__file__).resolve().parent) + "/service_modules"]
        for importer, module_name, ispkg in pkgutil.walk_packages(path=service_path):
            module = import_module(
                f"zambeze.orchestration.service_modules.{module_name}"
            )
            for attribute_name in dir(module):
                potential_service = getattr(module, attribute_name)
                if isclass(potential_service):
                    if (
                        issubclass(potential_service, service.Service)
                        and attribute_name != "Service"
                    ):
                        self._services[attribute_name.lower()] = potential_service()

    @property
    def registered(self) -> list:
        """List all services that have been registered.

        This method can be called at any time and is meant to simply display which
        packages are supported and present in the service_modules folder. It does
        not mean that these services have been configured. All services must be
        configured before they can be run.

        :return: Returns the names of all the services that have been registered
        :rtype: list[str]

        Examples
        Services services

        for service in services.registered:
            print(service)

        >>> globus
        >>> shell
        >>> rsync
        """
        services = []
        for key in self._services:
            services.append(deepcopy(key))
        return services

    def configure(self, config: dict, services: list[str] = ["all"]):
        """Configuration options for each service

        This method is responsible for initializing all the services that
        are supported in the service_modules folder. It should be called before the
        services can be run, all services should be configured before they can be
        run.

        :param config: This contains relevant configuration information for each service
        :type config: dict
        :param services: If provided will only register the services listed
        :type services: list[str]

        Example Arguments

        The configuration options for each service will appear under their name
        in the configuration parameter.

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
                    try:
                        obj = self._services.get(key)
                        obj.configure({})
                    except:
                        print(f"Unable to configure service {key} missing configuration options.")
                        raise
        else:
            for service in services:
                if service in config.keys():
                    self._services[service.lower()].configure(config[service.lower()])
                else:
                    try:
                        obj = self._services.get(key)
                        obj.configure({})
                    except:
                        print(f"Unable to configure service {key} missing configuration options.")
                        print("Configuration has the following content")
                        print(config)
                        print(f"{key} is not mentioned in the config so cannot associate configuration settings.")
                        raise

    @property
    def configured(self) -> list[str]:
        """Will return a list of all the services that have been configured.

        :return: list of all services that are ready to be run
        :rtype: list[str]
        """
        configured_services = []
        for key in self._services:
            obj = self._services.get(key)
            if obj.configured:
                configured_services.append(obj.name)

        return configured_services

    @property
    def info(self, services: list[str] = ["all"]) -> dict:
        """Will return the current state of the registered services

        :param services: the services to provide information about
        :default services: information about all services
        :type services: list[str]
        :return: The actual information of each service that was specified
        :rtype: dict

        Example Arguments

        services = ["globus", "shell"]

        Examples

        Services services
        services.configure(configuration_options)
        information = services.info
        print(information)

        >>> {
        >>>    "globus": {...}
        >>>    "shell": {...}
        >>> }
        """
        info = {}
        if "all" in services:
            for service in self._services.keys():
                info[service] = self._services[service].info
        else:
            for service in services:
                info[service] = self._services[service].info
        return info

    def run(self, arguments: dict, services: list[str] = ["all"]):
        """Run the services specified.

        :param arguments: the arguments to provide to each of the services that are to be run
        :type arguments: dict
        :param services: The list of all the services to run
        :type services: list[str]
        """
        if "all" in services:
            for key in self._services:
                if key in arguments.keys():
                    # If a package was passed to be processed"
                    self._services[key].process(arguments[key])
                else:
                    # else send an empty package"
                    self._services[key].process({})
        else:
            for service in services:
                if service in arguments.keys():
                    self._services[service.lower()].process(arguments[service])
                else:
                    self._services[service.lower()].process({})
