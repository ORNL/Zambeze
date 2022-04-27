import json
import uuid

# Local imports
import actions


class TaskExcept(Exception):
    pass


class Task:

    """it simply returns the french version"""

    _payload = {}

    def __init__(self, payload):
        if type(payload) is not dict:
            raise ActionExcept("Payload must be dict")
        self.__validatePayload(payload)
        self._payload = {
            "client_id": str(payload.get("client_id")),
            "task_id": str(payload.get("task_id")),
            "credentials": payload.get("credentials"),
            "action": actions.Factory(payload.get("action")).__dict__(),
        }

    def __validatePayload(self, payload):
        if payload.__contains__("client_id") == False:
            raise TaskExcept("Task missing client_id key")
        if payload.__contains__("task_id") == False:
            raise TaskExcept("Task missing task_id key")
        if payload.__contains__("credentials") == False:
            raise TaskExcept("Task missing credentials key")
        if payload.__contains__("action") == False:
            raise TaskExcept("Task missing action key")

        if type(payload.get("client_id")) is not uuid.UUID:
            raise TaskExcept("client_id must be of uuid.UUID type.")
        if type(payload.get("task_id")) is not uuid.UUID:
            raise TaskExcept("task_id must be of uuid.UUID type.")
        if type(payload.get("credentials")) is not dict:
            raise TaskExcept("credentials must be of dict type.")
        if type(payload.get("action")) is not dict:
            raise TaskExcept("action must be of dict type.")

    def display(self):
        print(json.dumps((self._payload), indent=4))

    def __str__(self):
        return str(self._payload)

    def __len__(self):
        return len(self._payload)
