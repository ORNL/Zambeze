from abc import ABCMeta, abstractmethod


class AbstractEntity(object, metaclass=ABCMeta):
    ID_FIELD_NAME = "stub"
    FIELD_NAMES = "stub"
    ENTITY_NAME = "stub"

    @abstractmethod
    def get_all_values(self):
        pass

    def __str__(self):
        return f"Entity values: {self.get_all_values()}"

    @abstractmethod
    def get_values_without_id(self):
        pass
