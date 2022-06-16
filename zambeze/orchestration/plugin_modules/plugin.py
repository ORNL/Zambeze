from abc import abstractmethod
from abc import ABC


class Plugin(ABC):
    """Abstract base class for ensuring that all registered plugins have the
    same interface"""

    def __init__(self):
        raise NotImplementedError(
            "process method of derived plugin must be implemented."
        )

    @abstractmethod
    def configure(self, config: dict):
        """Configure this set up the plugin."""
        raise NotImplementedError("for configuring plugin.")

    @property
    @abstractmethod
    def configured(self) -> bool:
        raise NotImplementedError(
            "Method for indicating if plugin has been configured has not been "
            "instantiated."
        )

    @property
    @abstractmethod
    def supportedActions(self) -> list[str]:
        raise NotImplementedError(
            "Method indicating supported actions of the plugin is not " "implemented"
        )

    @property
    @abstractmethod
    def help(self) -> str:
        raise NotImplementedError("Missing help message that explains plugin")

    @property
    @abstractmethod
    def info(self) -> dict:
        """This method is to be used after configuration step and will return
        information about the plugin such as configuration settings and
        defaults."""
        raise NotImplementedError("returns information about the plugin.")

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the plugin.

        The name of the plugin, should be lower case

        :return: name of the plugin
        :rtype: string
        """
        raise NotImplementedError(
            "name method of derived plugin must be " "implemented."
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

        checked_actions = plugin.check(arguments)

        for action in checked_actions:
            print(f"{action}: {checked_actions[action]}")

        >>> action1 True
        >>> action2 False
        """

    @abstractmethod
    def process(self, arguments: list[dict]) -> dict:
        """Will run the plugin with the provided arguments"""
        raise NotImplementedError(
            "process method of derived plugin must be implemented."
        )
