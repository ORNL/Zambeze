from abc import ABCMeta, abstractmethod


class AbstractEntity(object, metaclass=ABCMeta):
    ID_FIELD_NAME = "needs to be changed in the implementing class"
    FIELD_NAMES = "needs to be changed in the implementing class"
    ENTITY_NAME = "needs to be changed in the implementing class"

    def __str__(self):
        return f"Entity values: {self.get_all_values()}"

    @abstractmethod
    def get_all_values(self):
        raise NotImplementedError()

    @abstractmethod
    def get_values_without_id(self):
        raise NotImplementedError()
