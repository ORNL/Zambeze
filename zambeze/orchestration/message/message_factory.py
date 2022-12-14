# Local imports
from .abstract_message import AbstractMessage
from .activity_message.message_activity import MessageActivity
from .activity_message.message_activity_validator import MessageActivityValidator
from .activity_message.message_activity_template_generator import createActivityTemplate
from .status_message.message_status import MessageStatus
from .status_message.message_status_validator import MessageStatusValidator
from .status_message.message_status_template_generator import createStatusTemplate
from zambeze.orchestration.plugins_message_validator import PluginsMessageValidator
from zambeze.orchestration.plugins_message_template_engine import (
    PluginsMessageTemplateEngine,
)

from ..zambeze_types import MessageType, ActivityType

# Standard imports
import logging
from typing import Optional


class MessageFactory:
    def __init__(self, logger: Optional[logging.Logger] = None):

        self._logger = logger
        self._plugins_message_template_generators = PluginsMessageTemplateEngine(logger)
        self._plugins_message_validators = PluginsMessageValidator(logger)

    def createTemplate(
        self,
        message_type: MessageType,
        activity_type: ActivityType = ActivityType.SHELL,
        args={},
    ) -> tuple:
        """
        Will create a tuple with all the fields needed to build a message

        :param message_type: there are currently two supported message types
        status and activity.
        :type message_type: MessageType
        :param activity_type: The type of the activity
        :type activity_type: ActivityType enum
        :param args: additional arguments, i.e. the plugin and additional
        arguments needed by the plugin to pick an appropriate, or the shell
        if the shell activity was chosen
        template
        :type args: dict

        :return: the message outline and the MessageType which was passed in
        :rtype: (MessageType, dict)

        :Example:

        >>> factory = MessageFactory()
        >>> activity_msg_globus = factory.createTemplate(
        >>>                                          MessageType.ACTIVITY,
        >>>                                          ActivityType.PLUGIN,
        >>>                                          {plugin: "globus",
        >>>                                           action: "transfer"})
        >>> # In the print statement below the body: {} content is generated by
        >>> # the plugin.
        >>> print(activity_msg_globus[0].value)
        >>> ACTIVITY
        >>> print(activity_msg_globus[1])
        >>> {   "message_id": "",
        >>>     "type": "",
        >>>     "activity_id": "",
        >>>     "agent_id": "",
        >>>     "campaign_id": "",
        >>>     "credential": {},
        >>>     "submission_time": "",
        >>>     "body": {
        >>>       "type": "plugin",
        >>>       "plugin": "globus",
        >>>       "parameters": {
        >>>             "transfer": {
        >>>                "type": "synchronous",
        >>>                "items": [
        >>>                    {
        >>>                        "source": "globus://XXXXXXXX...X-XXXXXXXX/file1.txt",
        >>>                        "destination": "globus://YYY...YYYYYYYY/dest/file1.txt"
        >>>                    },
        >>>                    {
        >>>                        "source": "globus://XXXXXXXX-...XXXXXXXXXXXX/file2.txt",
        >>>                        "destination": "globus://YYYY...YYYYYYYY/dest/file2.txt"
        >>>                    }
        >>>                ]
        >>>                }
        >>>             }
        >>>         }
        >>>     },
        >>>     "needs": []
        >>> }
        """
        if message_type == MessageType.ACTIVITY:
            activity = createActivityTemplate(activity_type)

            if activity_type == ActivityType.PLUGIN:
                if "plugin" in args:
                    if args["plugin"] is not None:
                        activity.body.plugin = args["plugin"]
                        activity.body.parameters = (
                            self._plugins_message_template_generators.generate(
                                args["plugin"], args["action"]
                            )
                        )
                else:
                    raise Exception(
                        "Missing required arguments to initialize"
                        " PLUGIN activity i.e. args={'plugin': 'globus', 'action',"
                        " 'transfer'}"
                    )
            elif activity_type == ActivityType.SHELL:
                if "shell" in args:
                    activity.body.shell = args["shell"]
                else:
                    raise Exception(
                        "Missing required arguments to initialize"
                        " SHELL activity i.e. args={'shell': 'bash'}"
                    )

            return (message_type, activity)

        elif message_type == MessageType.STATUS:
            status = createStatusTemplate()
            return (message_type, status)
        else:
            raise Exception(
                "Unrecognized message type cannot createTemplate: "
                f"{message_type.value}"
            )

    def create(self, args: tuple) -> AbstractMessage:
        """Is responsible for creating a Message

        The tuple must be of the form:

        ( MessageType, {} )

        The createTemplate method can be called to generate a suitable tuple
        that the create method will accept.

        :Example:

        ( MessageType.ACTIVITY, activity_msg )

        ```python
        factory = MessageFactory()
        msg_template = factory.createTemplate(
                                MessageType.ACTIVITY,
                                "rsync",
                                "transfer")

        msg = factory.create(msg_template)
        ```

        """

        if len(args) != 2:
            raise Exception(
                "Malformed input, create method expects tuple of" "length 2"
            )

        if args[0] == MessageType.ACTIVITY:
            validator = MessageActivityValidator()
            result = validator.check(args[1])
            print(result)
            if result[0]:
                if args[1].body.type == "PLUGIN":
                    plugin_name = args[1].body.plugin
                    results = self._plugins_message_validators.validate(
                        plugin_name, args[1].body.parameters
                    )
                    print(f"Printing results {results}")
                    # Search through the results of the validator checks
                    # { rsync: [{"action": (False, "message")}] }
                    for check in results[plugin_name]:
                        for action in check.keys():
                            if check[action][0] is False:
                                raise Exception(
                                    "Invalid plugin message body" f"{check[action][1]}"
                                )
                return MessageActivity(args[1], self._logger)
            else:
                raise Exception(f"Invalid activity message: {result[1]}")
        elif args[0] == MessageType.STATUS:
            validator = MessageStatusValidator()
            result = validator.check(args[1])
            if result[0]:
                return MessageStatus(args[1])
            else:
                raise Exception(f"Invalid status message: {result[1]}")
        else:
            raise Exception(
                "Unrecognized message type cannot instantiate: " f"{args[0].value}"
            )
