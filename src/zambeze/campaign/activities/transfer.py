from .abstract_activity import Activity
import uuid
import time

from zambeze.orchestration.message.abstract_message import AbstractMessage
from zambeze.orchestration.message.message_factory import MessageFactory
from zambeze.orchestration.zambeze_types import MessageType, ActivityType


class TransferActivity(Activity):
    def __init__(self, name, source_target, dest_directory, override_existing=False):
        self.name = name
        self.source_target = source_target
        self.dest_directory = dest_directory
        self.override_existing = override_existing

        super().__init__(
            name="TRANSFER",
            activity_id=str(uuid.uuid4()),
            source_target=self.source_target,
            dest_directory=self.dest_directory,
            override_existing=self.override_existing,
        )

        self.type = "TRANSFER"

    def generate_message(self) -> AbstractMessage:
        factory = MessageFactory(logger=self.logger)
        template = factory.create_template(
            MessageType.ACTIVITY, ActivityType.TRANSFER, {"transfer_software": "globus"}
        )

        try:
            template[1].source_file = self.source_file
            template[1].dest_directory = self.dest_directory
            template[1].override_existing = self.override_existing
            template[1].activity_id = self.activity_id
            template[1].message_id = self.message_id
            template[1].origin_agent_id = self.origin_agent_id
            template[1].campaign_id = self.campaign_id
            template[1].type = "TRANSFER"

            # TODO: should probably fill this with globus token
            template[1].credential = {}

            template[1].submission_time = str(int(time.time()))

            # Not sure why this line is necessary if we have template
            template[1].body.transfer_software = "globus"

            template[1].body.files = self.files
        except Exception as e:
            self.logger.info(f"[oogily boogily] Error is here: {e}")

        return factory.create(template)
