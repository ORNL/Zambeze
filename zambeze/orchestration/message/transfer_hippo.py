import os
import time
import socket
import getpass
import pathlib

from dataclasses import asdict
from zambeze.orchestration.zambeze_types import MessageType, ActivityType
from zambeze.orchestration.message.message_factory import MessageFactory


class TransferHippo:
    def __init__(self, agent_id, settings, logger):

        self._logger = logger
        self._settings = settings
        self._agent_id = agent_id
        self._msg_factory = MessageFactory(logger=self._logger)

    def pack(self, transfer_type, file_url, activity_id, campaign_id):
        """Use templates to pack a transfer hippo with file(s) to move."""

        messages = []

        if transfer_type == "globus":

            self._logger.info(
                f"Starting Globus configuration for file at {file_url.path}"
            )

            # Check if we have plugin
            source_file_name = os.path.basename(file_url.path)
            default_endpoint = self._settings.settings["plugins"]["globus"]["config"][
                "default_endpoint"
            ]

            default_working_dir = self._settings.settings["plugins"]["All"][
                "default_working_directory"
            ]
            print(f"default working directory {default_working_dir}")

            local_globus_uri = (
                f"globus://{default_endpoint}{os.sep}" f"source_file_name"
            )

            local_posix_uri = (
                f"file://{default_working_dir}{os.sep}" f"{source_file_name}"
            )

            msg_template_transfer = self._msg_factory.createTemplate(
                MessageType.ACTIVITY,
                ActivityType.PLUGIN,
                {"plugin": "globus", "action": "transfer"},
            )

            # msg_template_transfer[1].message_id = str(uuid.uuid4())
            msg_template_transfer[1].activity_id = activity_id
            msg_template_transfer[1].agent_id = self._agent_id
            msg_template_transfer[1].campaign_id = campaign_id
            msg_template_transfer[1].credential = {}
            msg_template_transfer[1].submission_time = str(int(time.time()))
            msg_template_transfer[1].body.transfer.type = "synchronous"
            msg_template_transfer[1].body.transfer.items[0].source = file_url.geturl()
            msg_template_transfer[1].body.transfer.items[0].destination = (
                local_globus_uri,
            )

            self._logger.debug(
                f"Creating mutable message of: {asdict(msg_template_transfer)}"
            )
            # Will validate the message fields and then make it immutable
            immutable_msg = self._msg_factory.create(msg_template_transfer)

            checked_result = self._settings.plugins.check(immutable_msg)
            self._logger.debug(checked_result)

            # Move from the Globus collection to the default working
            # directory
            move_tmpl8 = self._msg_factory.createTemplate(
                MessageType.ACTIVITY,
                ActivityType.PLUGIN,
                {"plugin": "globus", "action": "move_from_globus_collection"},
            )

            # TODO: we can't have names this long AND an 88 char width limit...
            # TODO: shorten 'move_to_globus_connection'
            # TODO: 'source' and 'dest'.
            # TODO: 'submit_time'.
            # move_tmpl8[1].message_id = str(uuid.uuid4())
            move_tmpl8[1].activity_id = activity_id
            move_tmpl8[1].agent_id = self._agent_id
            move_tmpl8[1].campaign_id = campaign_id
            move_tmpl8[1].credential = {}
            move_tmpl8[1].submission_time = str(int(time.time()))
            move_tmpl8[1].body.move_to_globus_collection.items[
                0
            ].source = local_globus_uri
            move_tmpl8[1].body.move_to_globus_collection.items[
                0
            ].destination = local_posix_uri

            # Make the message immutable.
            immutable_msg_move = self._msg_factory.create(move_tmpl8)

            messages.append(immutable_msg)
            messages.append(immutable_msg_move)

        elif transfer_type == "rsync":
            msg_template = self._msg_factory.createTemplate(
                MessageType.ACTIVITY,
                ActivityType.PLUGIN,
                {"plugin": "rsync", "action": "transfer"},
            )

            # TODO: ip addr and path should be refactored into a 'source_uri'.
            # Pack the message template with rsync-specific information.
            msg_template[1].body.transfer.items[0].source.ip = file_url.netloc
            msg_template[1].body.transfer.items[0].source.path = file_url.path
            msg_template[1].body.transfer.items[0].source.username = file_url.username
            msg_template[1].body.transfer.items[
                0
            ].destination.ip = socket.gethostbyname(socket.gethostname())
            msg_template[1].body.transfer.items[0].destination.path = str(
                pathlib.Path().resolve()
            )
            msg_template[1].body.transfer.items[
                0
            ].destination.username = getpass.getuser()
            # Will validate the message fields and then make it immutable
            msg = self._msg_factory.create(msg_template)

            messages.append(msg)

        # if not transfer type, then we leave messages empty.
        elif transfer_type is None:
            self._logger.info("Local file; creating no activity messages!")

        return messages
