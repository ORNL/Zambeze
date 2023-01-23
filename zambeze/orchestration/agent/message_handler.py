import pickle
import threading
import time
import dill
import zmq

from queue import Queue

from zambeze.orchestration.db.model.activity_model import ActivityModel
from zambeze.orchestration.db.dao.activity_dao import ActivityDAO
from zambeze.orchestration.message.abstract_message import AbstractMessage

from zambeze.orchestration.queue.queue_factory import QueueFactory
from zambeze.orchestration.zambeze_types import QueueType, MessageType

from .temp_activity_to_plugin_map import activity_to_plugin_map


class MessageHandler(threading.Thread):
    def __init__(self, agent_id, settings, logger):
        threading.Thread.__init__(self)
        self.agent_id = agent_id
        self._settings = settings
        self._logger = logger

        self.mq_args = {
            "ip": self._settings.settings["rmq"]["host"],
            "port": self._settings.settings["rmq"]["port"],
        }

        self._logger.info("EARTH TO JOSH C")

        self.queue_factory = QueueFactory(logger=self._logger)

        self._logger.info(
            "[Message Handler] RabbitMQ broker and channel both created successfully!"
        )

        self._activity_dao = ActivityDAO(self._logger)

        self._zmq_context = zmq.Context()
        self._zmq_socket = self._zmq_context.socket(zmq.REP)
        self._logger.info(
            "[Message Handler] Binding to ZMQ: "
            f"{self._settings.get_zmq_connection_uri()}"
        )
        self._zmq_socket.bind(self._settings.get_zmq_connection_uri())

        # Queues to allow safe inter-thread communication.
        self.msg_handler_send_activity_q = Queue()
        self.check_activity_q = Queue()
        self.send_control_q = Queue()
        self._recv_control_q = Queue()

        self._logger.info("[Message Handler] Message handler successfully initialized!")

        # THREAD 1: recv activities from campaign
        campaign_listener = threading.Thread(
            target=self.recv_activities_from_campaign, args=()
        )
        # THREAD 2: recv activities from rmq
        activity_listener = threading.Thread(target=self.recv_activity, args=())
        # THREAD 3: recv control from RMQ
        control_listener = threading.Thread(target=self.recv_control, args=())
        # THREAD 4: send activity to RMQ
        activity_sender = threading.Thread(target=self.send_activity, args=())

        campaign_listener.start()
        activity_listener.start()
        control_listener.start()
        activity_sender.start()

    def recv_activities_from_campaign(self):
        """
        >> Async

        Receives message from campaign on ZMQ socket, saves in send_activity_q
        """

        while True:
            self._logger.info(
                "[recv_activities_from_campaign] Waiting for messages from campaign..."
            )

            # Use ZMQ to receive activities from campaign.
            activity_bytestring = self._zmq_socket.recv()
            self._zmq_socket.send(b"FOOBAR")  # TODO... send something cleaner.
            self._logger.debug(
                "[recv_activities_from_campaign] Received an activity bytestring!"
            )
            activity = pickle.loads(activity_bytestring)

            activity.agent_id = self.agent_id

            self._logger.debug(f"Here is the activity: {activity}")

            try:
                activity_message: AbstractMessage = activity.generate_message()

            except Exception as e:
                self._logger.error(f"CANT GENERATE MESSAGE IN MSG HANDLER! {e}")

            self._logger.info(
                "[recv_activities_from_campaign] Dispatching message "
                f"activity_id: {activity.activity_id} "
                f"message_id: {activity_message.data.message_id}")
            self._logger.debug(
                "[recv_activities_from_campaign] Received message from "
                f"campaign: {activity_message}"
            )

            activity_model = ActivityModel(
                agent_id=str(self.agent_id), created_at=int(time.time() * 1000)
            )
            self._logger.debug(
                "[recv_activities_from_campaign] Creating activity in the"
                f" DB: {activity}"
            )
            self._activity_dao.insert(activity_model)
            self._logger.debug("[recv_activities_from_campaign] Saved in the DB!")

            self.msg_handler_send_activity_q.put(activity_message)

    # Custom RabbitMQ callback; made decision to put here so that we can
    # access the messages.
    def _callback(self, ch, method, properties, body):
        self._logger.info("[recv_activity] receiving activity...")
        activity = dill.loads(body)

        # TODO: is this doing anything?
        self.check_activity_q.put(activity)

        if activity.type != MessageType.ACTIVITY:
            # TODO: I don't think this is necessary, as we're pulling from activity
            # channel...
            print("Non activity detected")
            self._logger.debug("Non-activity message received on" "ACTIVITY channel")

        # TODO: should be able to require a list of plugins (not just one).
        # TODO: move these to agent-init.

        required_plugin = activity_to_plugin_map[activity.data.body.type]
        # cmd_str =

        plugins_are_configured = self.are_plugins_configured(required_plugin)
        # plugins_are_ready = self.message_to_plugin_validator(required_plugin,
        #                                                      cmd=activity['cmd'])

        should_ack = plugins_are_configured  # and plugins_are_ready

        # TODO: additional functionalities
        #
        # 1. Pulling down messages based on metadata filters rather than pulling
        # down anything.
        #
        # 2. Initial 'broadcast' check to see if there is a single agent capable
        # of running each activity?
        #
        # 3. Agent thinks it can run activity. Hits some sort of failure case
        # (either in execution or configuration) ... wrap this up as a new
        # Error-flag activity, and let it be handled accordingly.
        #
        # ROUTING: https://www.rabbitmq.com/tutorials/tutorial-four-python.html

        self._logger.debug(
            f"Should ack: {should_ack} | Plugins Configured: {plugins_are_configured}"
        )
        did_except = False
        try:
            if should_ack:
                ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
                self._logger.debug("[recv activity] ACKED message.")
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, multiple=False)
                self._logger.debug("[recv activity] NACKED message.")
                # stuck in NACK loop.
                time.sleep(1)  # TODO !!!!!!!!!!!!!
        except Exception as e:
            did_except = True
            self._logger.error(f"[Message Handler] AG CAUGHT: {e}")

        # Test line to see if this function is reaching here without exception
        with open("/Users/6o1/Desktop/file.txt", "w") as f:
            f.write(f"IN CALLBACK: {should_ack} | {did_except}")

    def recv_activity(self):
        """
        >> Async

        Get activity from 'ACTIVITIES' queue.
        If we have the correct plugins, then we keep it (ack). Otherwise, we
        put it back (nack).
        """

        self._logger.info(
            "[Message Handler] Connecting to RabbitMQ RECV ACTIVITY broker..."
        )
        queue_client = self.queue_factory.create(QueueType.RABBITMQ, self.mq_args)
        queue_client.connect()

        self._logger.debug(" [*] Waiting for ACTIVITY messages. To exit press CTRL+C")
        queue_client.listen_and_do_callback(
            callback_func=self._callback,
            channel_to_listen="ACTIVITIES",
            should_auto_ack=False,
        )

    def send_activity(self):
        """
        (from agent.py) input activity; send to "ACTIVITIES" queue.
        """

        self._logger.info(
            "[Message Handler] Connecting to RabbitMQ SEND ACTIVITY broker..."
        )
        queue_client = self.queue_factory.create(QueueType.RABBITMQ, self.mq_args)
        queue_client.connect()

        while True:
            self._logger.info("[send_activity] Waiting for messages...")
            activity_msg = self.msg_handler_send_activity_q.get()
            self._logger.info("HOY")
            # activity_msg = activity.generate_message()

            self._logger.info(
                "[send_activity] Dispatching message "
                f"activity_id: {activity_msg.data.activity_id} "
                f"message_id: {activity_msg.data.message_id}")

            # TODO: need to unpack the message in the print...
            self._logger.info(f"[send_activity] {activity_msg}")

            self._logger.info("[send_activity] Message received! Sending...")
            try:
                queue_client.send(exchange="", channel="ACTIVITIES", body=activity_msg)
            except Exception as e:
                self._logger.error(f"CAUGHT: {e}")
            self._logger.debug("[send_activity] Successfully sent activity!")

    def recv_control(self):
        """
        Receive messages from the control channel!
        """

        self._logger.info(
            "[Message Handler] Connecting to RabbitMQ RECV CONTROL broker..."
        )
        queue_client = self.queue_factory.create(QueueType.RABBITMQ, self.mq_args)
        queue_client.connect()

        self._logger.info("[recv_control] receiving activity...")

        def callback(_1, _2, _3, body):
            activity = pickle.loads(body)
            self._logger.info(" [x recv_activity] Received %r" % activity)
            self._recv_control_q.put(activity)

        queue_client.listen_and_do_callback(
            channel_to_listen="CONTROL", callback_func=callback, should_auto_ack=True
        )

    def send_control(self):
        """
        (from agent.py) input control message; send to "CONTROL" queue.
        """

        self._logger.info(
            "[Message Handler] Connecting to RabbitMQ SEND CONTROL broker..."
        )
        queue_client = self.queue_factory.create(QueueType.RABBITMQ, self.mq_args)
        queue_client.connect()

        while True:
            self._logger.debug("[send_activity] Waiting for messages...")
            activity_msg = self.msg_handler_send_activity_q.get()

            self._logger.debug("[send_activity] Message received! Sending...")
            try:
                queue_client.send(exchange="", channel="CONTROL", body=activity_msg)
            except Exception as e:
                self._logger.info(f"Caught error: {e}")
            self._logger.info("[send_activity] Successfully sent activity!")

    def message_to_plugin_validator(self, plugin, cmd):
        """Determine whether plugin can execute based on plugin input schema.

        # Running Checks
        # Returned results should be double nested dict with a tuple of
        # the form
        #
        # "plugin": { "action": (bool, message) }
        #
        # The bool is a true or false which indicates if the action
        # for the plugin is a problem, the message is an error message
        # or a success statement
        """

        checked_result = self._settings.plugins.check(plugin_name=plugin, arguments=cmd)
        self._logger.debug(f"Checked result: {checked_result}")
        # return whether NO errors were detected.
        return not checked_result.error_detected()

    def are_plugins_configured(self, plugin_label):
        return self._settings.is_plugin_configured(plugin_label)
