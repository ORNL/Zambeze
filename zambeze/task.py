import json
import uuid

# Local imports
from . import actions


class TaskExcept(Exception):
    pass


class Task:

    """it simply returns the french version"""

    _payload = {}

    def __init__(self, payload):
        if type(payload) is not dict:
            raise actions.ActionExcept("Payload must be dict")
        self.__validatePayload(payload)
        self._payload = {
            "client_id": str(payload.get("client_id")),
            "task_id": str(payload.get("task_id")),
            "credentials": payload.get("credentials"),
            "action": actions.Factory(payload.get("action")).__dict__(),
        }

    def __validatePayload(self, payload):
        if not payload.__contains__("client_id"):
            raise TaskExcept("Task missing client_id key")
        if not payload.__contains__("task_id"):
            raise TaskExcept("Task missing task_id key")
        if not payload.__contains__("credentials"):
            raise TaskExcept("Task missing credentials key")
        if not payload.__contains__("action"):
            raise TaskExcept("Task missing action key")

        if not isinstance(payload.get("client_id"), uuid.UUID):
            raise TaskExcept("client_id must be of uuid.UUID type.")
        if not isinstance(payload.get("task_id"), uuid.UUID):
            raise TaskExcept("task_id must be of uuid.UUID type.")
        if not isinstance(payload.get("credentials"), dict):
            raise TaskExcept("credentials must be of dict type.")
        if not isinstance(payload.get("action"), dict):
            raise TaskExcept("action must be of dict type.")

    def display(self):
        print(json.dumps((self._payload), indent=4))

    def __str__(self):
        return str(self._payload)

    def __len__(self):
        return len(self._payload)
