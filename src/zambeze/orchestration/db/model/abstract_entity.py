from abc import ABCMeta, abstractmethod


class AbstractEntity(object, metaclass=ABCMeta):
    @classmethod
    @property
    @abstractmethod
    def ID_FIELD_NAME(cls) -> str:
        raise NotImplementedError()

    @classmethod
    @property
    @abstractmethod
    def FIELD_NAMES(cls) -> str:
        raise NotImplementedError()

    @classmethod
    @property
    @abstractmethod
    def ENTITY_NAME(cls) -> str:
        raise NotImplementedError()

    def __str__(self):
        return f"Entity values: {self.get_all_values()}"

    @abstractmethod
    def get_all_values(self):
        raise NotImplementedError()

    @abstractmethod
    def get_values_without_id(self):
        raise NotImplementedError()
