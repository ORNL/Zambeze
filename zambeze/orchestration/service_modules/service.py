from abc import abstractmethod
from abc import ABC


class Service(ABC):
    """Abstract base class for ensuring that all registered services have the
    same interface"""

    def __init__(self):
        raise NotImplementedError(
            "process method of derived service must be implemented."
        )

    @abstractmethod
    def configure(self, config: dict):
        """Configure this set up the service."""
        raise NotImplementedError("for configuring service.")

    @property
    @abstractmethod
    def configured(self) -> bool:
        raise NotImplementedError(
            "Method for indicating if service has been configured has not been "
            "instantiated."
        )

    @property
    @abstractmethod
    def supportedActions(self) -> list[str]:
        raise NotImplementedError(
            "Method indicating supported actions of the service is not " "implemented"
        )

    @property
    @abstractmethod
    def help(self) -> str:
        raise NotImplementedError("Missing help message that explains plugin")

    @property
    @abstractmethod
    def info(self) -> dict:
        """This method is to be used after configuration step and will return
        information about the service such as configuration settings and
        defaults."""
        raise NotImplementedError("returns information about the service.")

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the service.

        The name of the service, should be lower case

        :return: name of the service
        :rtype: string
        """
        raise NotImplementedError(
            "name method of derived service must be " "implemented."
        )

    @abstractmethod
    def check(self, arguments: list[dict]) -> dict:
        """Determine if the proposed arguments can be executed by this instance.

        :param arguments: The arguments are checked to ensure their types and
        formats are valid
        :type arguments: list[dict]
        :return: Returns the list of actions that are vaid
        :rtype: dict with the actions valid actions listed with bool set to
        True and invalid ones False

        Example Arguments

        arguments =
        [
            { "action1": { "dothis": ...} },
            { "action2": { "dothat": ...} },
        ]

        Example

        checked_actions = service.check(arguments)

        for action in checked_actions:
            print(f"{action}: {checked_actions[action]}")

        >>> action1 True
        >>> action2 False
        """

    @abstractmethod
    def process(self, arguments: list[dict]):
        """Will run the service with the provided arguments"""
        raise NotImplementedError(
            "process method of derived service must be implemented."
        )
