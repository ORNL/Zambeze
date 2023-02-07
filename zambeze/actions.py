import json
import uuid


class ActionExcept(Exception):
    pass


class DataActionExcept(ActionExcept):
    pass


class ControlActionExcept(ActionExcept):
    pass


class ComputeActionExcept(ActionExcept):
    pass


class Action:
    _payload = {}

    def display(self):
        print(json.dumps(self._payload, indent=4))

    def __str__(self):
        return str(self._payload)

    def __dict__(self):
        return self._payload


class ControlAction(Action):
    _payload = {}

    def __init__(self, payload):
        super().__init__()
        if not isinstance(payload, dict):
            raise ActionExcept("Payload must be dict")
        self.__validatePayload(payload)
        self._payload = {
            "type": payload.get("type"),
            "target_id": str(payload.get("target_id")),
            "task_id": str(payload.get("task_id")),
            "body": payload.get("body"),
        }

    def __validatePayload(self, payload):
        if not payload.__contains__("type"):
            raise ControlActionExcept("Control action missing type key")
        if not payload.__contains__("target_id"):
            raise ControlActionExcept("Control action missing target_id key")
        if not payload.__contains__("task_id"):
            raise ControlActionExcept("Control action missing task_id key")
        if not payload.__contains__("body"):
            raise ControlActionExcept("Control action missing body key")

        if not isinstance(payload.get("target_id"), uuid.UUID):
            raise ControlActionExcept("target_id must be of uuid.UUID type.")
        if not isinstance(payload.get("task_id"), uuid.UUID):
            raise ControlActionExcept("task_id must be of uuid.UUID type.")


class DataAction(Action):
    """it simply returns the spanish version"""

    def __init__(self, payload):
        super().__init__()
        if not isinstance(payload, dict):
            raise ActionExcept("Payload must be dict")
        self.__validatePayload(payload)
        self._payload = payload

    def __validatePayload(self, payload):
        if not payload.__contains__("type"):
            raise DataActionExcept("Data action missing type key")
        if not payload.__contains__("source"):
            raise DataActionExcept("Data action missing source key")
        if not payload.__contains__("destination"):
            raise DataActionExcept("Data action missing destination key")


class ComputeAction(Action):
    def __init__(self, payload):
        super().__init__()
        if not isinstance(payload, dict):
            raise ActionExcept("Payload must be dict")
        self.__validatePayload(payload)

        self._payload = {
            "type": payload.get("type"),
            "workflow_id": str(payload.get("workflow_id")),
            "parameters": payload.get("parameters"),
        }

    def __validatePayload(self, payload):
        if not payload.__contains__("type"):
            raise DataActionExcept("Compute action missing type key")
        if not payload.__contains__("workflow_id"):
            raise DataActionExcept("Compute action missing workflow_id key")
        if not payload.__contains__("parameters"):
            raise DataActionExcept("Compute action missing parameters key")

        if not isinstance(payload.get("workflow_id"), uuid.UUID):
            raise ComputeActionExcept("workflow_id must be of UUID type.")
        if not isinstance(payload.get("parameters"), dict):
            raise ComputeActionExcept("parameters must be of dict type.")


def Factory(payload):
    """Factory Method"""
    actions = {"Control": ControlAction, "Data": DataAction, "Compute": ComputeAction}

    return actions[payload.get("type")](payload)
