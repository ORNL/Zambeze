import uuid
import time

from zambeze.orchestration.message.abstract_message import AbstractMessage
from zambeze.orchestration.message.message_factory import MessageFactory
from zambeze.orchestration.zambeze_types import MessageType, ActivityType


class TransferActivity:
    """A file transfer activity.

    Attributes
    ----------
    name : str
        Name of the transfer activity.
    source_file : str
        Source file that will be transferred.
    dest_directory : str
        Destination directory for the source file.
    override_existing : bool
        Overwrite files and/or directories at destination. Default is False.
    activity_id : str
        ID for the transfer activity.

    Methods
    -------
    generate_message
        Generate a message for the transfer activity.
    """

    def __init__(
        self,
        name: str,
        source_file: str,
        dest_directory: str,
        override_existing: bool = False,
    ):
        self.name = name
        self.source_file = source_file
        self.dest_directory = dest_directory
        self.override_existing = override_existing

        self.name = "TRANSFER"
        self.activity_id = str(uuid.uuid4())

    def generate_message(self) -> AbstractMessage:
        """Generate a message for the transfer activity."""

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
            template[1].agent_id = self.agent_id
            template[1].campaign_id = self.campaign_id

            # TODO: should probably fill this with globus token
            template[1].credential = {}

            template[1].submission_time = str(int(time.time()))
            template[1].body.type = "TRANSFER"

            # Not sure why this line is necessary if we have template
            template[1].body.transfer_software = "globus"

            template[1].body.files = self.files
        except Exception as e:
            self.logger.info(f"[oogily boogily] Error is here: {e}")

        return factory.create(template)
