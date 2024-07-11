# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import time
import uuid

from datetime import datetime
from zambeze.orchestration.message.abstract_message import AbstractMessage
from zambeze.orchestration.message.message_factory import MessageFactory
from zambeze.orchestration.zambeze_types import MessageType, ActivityType


class ShellActivity:
    def __init__(
        self,
        name: str,
        files: list[str],
        command: str,
        arguments: str,
        logger: logging.Logger | None = None,
        env_vars: dict[str, str] | None = None,
        campaign_id: str | None = None,
        message_id: str | None = None,
        origin_agent_id: str | None = None,
        running_agent_ids: list[str] | None = None,
    ):
        self.name = name
        self.files = files
        self.command = command
        self.arguments = arguments.split(" ")
        self.logger = logger
        self.env_vars = env_vars
        self.campaign_id = campaign_id
        self.message_id = message_id
        self.origin_agent_id = origin_agent_id

        self.running_agent_ids = (
            running_agent_ids if running_agent_ids is not None else []
        )

        self.activity_id = str(uuid.uuid4())
        self.type = "SHELL"
        self.submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        self.plugin_args = {
            "shell": "bash",
            "parameters": {
                "command": self.command,
                "args": self.arguments,
                "env_vars": self.env_vars,
            },
        }

    def generate_message(self) -> AbstractMessage:
        """
        Create a message from a factory template.
        """
        factory = MessageFactory(logger=self.logger)

        template = factory.create_template(
            MessageType.ACTIVITY, ActivityType.SHELL, {"shell": "bash"}
        )

        try:
            print("<< try here >>", self.origin_agent_id)
            # These go into every activity.
            template[1].origin_agent_id = self.origin_agent_id
            template[1].running_agent_ids = self.running_agent_ids
            template[1].activity_id = self.activity_id
            template[1].message_id = self.message_id
            template[1].campaign_id = self.campaign_id
            template[1].credential = {}
            template[1].submission_time = str(int(time.time()))

            # These go into just SHELL activities.
            template[1].body.type = "SHELL"
            template[1].body.shell = "bash"
            template[1].body.files = self.files
            template[1].body.parameters.program = self.command
            template[1].body.parameters.args = self.arguments
            template[1].body.parameters.env_vars = self.env_vars
        except Exception as e:
            print("<< except here >>")
            self.logger.info(f"Error is here: {e}")

        return factory.create(template)
