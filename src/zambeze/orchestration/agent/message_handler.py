import pickle
import threading
import time
import zmq

from queue import Queue

from zambeze.orchestration.db.model.activity_model import ActivityModel
from zambeze.orchestration.db.dao.activity_dao import ActivityDAO
from zambeze.orchestration.queue.queue_factory import QueueFactory
from zambeze.orchestration.zambeze_types import QueueType
from zambeze.campaign.activities.dag import DAG

from .temp_activity_to_plugin_map import activity_to_plugin_map


class MessageHandler(threading.Thread):
    """Message Handler is a persistent series of threads that
    handles all message queue communication in Zambeze.

    Parameters
    ----------
    agent_id : str
        uuid-style string representing the agent on which the handler is running
    settings: zambeze.src.settings.Settings
        loaded Zambeze settings object
    logger: logging.Logger
        zambeze core file logger.
    """
    def __init__(self, agent_id, settings, logger):
        threading.Thread.__init__(self)

        self.agent_id = agent_id
        self._settings = settings
        self._logger = logger

        self.mq_args = {
            "ip": self._settings.settings["rmq"]["host"],
            "port": self._settings.settings["rmq"]["port"],
        }

        self.queue_factory = QueueFactory(logger=self._logger)

        self._logger.info("[mh] RabbitMQ broker and channel both created successfully!")

        self._activity_dao = ActivityDAO(self._logger)

        self._zmq_context = zmq.Context()
        self._zmq_socket = self._zmq_context.socket(zmq.REP)
        self._logger.info("[mh] Binding to random ZMQ port...")

        # Bind to a random available port in the range 60000-65000
        port_message = self._zmq_socket.bind_to_random_port(
            "tcp://*", min_port=60000, max_port=65000
        )

        # Set ZMQ port in settings (and flush to file)
        self._settings.settings["zmq"]["port"] = port_message
        self._settings.flush()

        self._logger.info(f"[mh] Advertised port in agent.yaml file: {port_message}")

        # Queues to allow safe inter-thread communication.
        self.msg_handler_send_activity_q = Queue()
        self.msg_handler_send_control_q = Queue()
        self.recv_control_q = Queue()
        self.check_activity_q = Queue()

        self._logger.info("[mh] Message handler successfully initialized!")

        # THREAD 1: recv activities from campaign
        campaign_listener = threading.Thread(
            target=self.recv_activity_dag_from_campaign, args=()
        )

        # THREAD 2: recv activities from rmq
        activity_listener = threading.Thread(target=self.recv_activity, args=())
        # THREAD 3: recv control from RMQ
        control_listener = threading.Thread(target=self.recv_control, args=())
        # THREAD 4: recv control from RMQ
        control_sender = threading.Thread(target=self.send_control, args=())
        # THREAD 5: send activity to RMQ
        activity_sender = threading.Thread(target=self.send_activity_dag, args=())

        if (
            "flowcept" in self._settings.settings
            and self._settings.settings["flowcept"]["config"]["active"]
        ):
            self._logger.info("[mh] Flowcept active. Loading libraries!")
            from flowcept import ZambezeInterceptor, FlowceptConsumerAPI

            fc_interceptor = ZambezeInterceptor()
            self.fc_consumer = FlowceptConsumerAPI(fc_interceptor)
            self.fc_consumer.start()
            self._logger.info("[mh] Flowcept libraries succesfully loaded.")

        campaign_listener.start()
        activity_listener.start()
        control_listener.start()
        activity_sender.start()
        control_sender.start()

    def recv_activity_dag_from_campaign(self):
        """Receive the activity graph from the campaign and send its activity nodes to
        the appropriate queues.
        """

        while True:
            self._logger.info(
                "[recv_activities_from_campaign] Waiting for messages from campaign..."
            )

            # Use ZMQ to receive activities from campaign.
            dag_bytestring = self._zmq_socket.recv()
            self._zmq_socket.send(b"Notification of activity-dag receipt by ZMQ...")
            self._logger.debug(
                "[recv_activity_dag_from_campaign] Received an activity DAG bytestring!"
            )

            # try:
            activity_dag = DAG.deserialize_dag(dag_bytestring)

            self._logger.debug(
                f"[recv_activity_dag_from_campaign] Received message from campaign: {activity_dag}"
            )

            # Iterating over nodes in NetworkX DAG
            num_activities = 0
            is_monitor = False
            is_terminator = False
            for activity_id, node_data in activity_dag.nodes(data=True):
                if activity_id == "MONITOR":
                    node_data["all_activity_ids"] = activity_dag.get_node_ids()
                    is_monitor = True
                if activity_id == "TERMINATOR":
                    is_terminator = True

                # If not monitor or terminator
                try:
                    if (not is_monitor) or (not is_terminator):
                        self._logger.info("[mh] Flushing activity message to flowcept")
                        node_data["activity"].origin_agent_id = self.agent_id
                        node_data["activity_status"] = "SUBMITTED"

                except Exception as e:
                    self._logger.error(e)

                self._logger.info(
                    f"[message_handler] The activity_node to send...:\n{(activity_id, node_data)}"
                )

                activity_model = ActivityModel(
                    agent_id=str(self.agent_id), created_at=int(time.time() * 1000)
                )
                self._activity_dao.insert(activity_model)
                self._logger.debug("[recv_activity_dag_from_campaign] Saved in the DB!")

                self.msg_handler_send_activity_q.put((activity_id, node_data))
                num_activities += 1
                self._logger.debug("[recv_activity_dag_from_campaign] Sent node!")

            self._logger.info(
                f"[message_handler] Number of activities sent for campaign: {num_activities}"
            )

    def _callback(self, ch, method, _properties, body):
        """RabbitMQ callback method to process messages from the ACTIVITIES message queue.
        Determines whether to acknowledge (ACK) or not acknowledge (NACK) each message based on
        whether the required plugins are configured and the actions are supported.

        Parameters
        ----------
        ch : pika.channel.Channel
            The channel instance from RabbitMQ used to send the ACK/NACK decision.
        method : pika.spec.Basic.Deliver
            Delivery method containing delivery metadata, such as the delivery tag used in ACK/NACK.
        _properties : pika.spec.BasicProperties
            Message properties, not used in this function but required by the callback signature.
        body : bytes
            The message body which is expected to be a serialized DAG node that specifies the activity.
        """
        self._logger.debug(
            "[mh-recv-activity] Processing callback function for activity queue recv."
        )
        activity_node = DAG.deserialize_node(body)
        self._logger.info(f"[mn-recv-activity] receiving activity...{activity_node}")

        # Anyone can monitor or terminate.
        if activity_node[0] in ["MONITOR", "TERMINATOR"]:
            plugins_are_configured = True
            actions_are_supported = True
            self._logger.info(
                f"[mh] Zambeze activity received of ID: {activity_node[0]}"
            )

        else:
            try:
                self._logger.info("[mh] Unpacking activity info from queue...")
            except Exception as e:
                self._logger.error(e)

            try:
                required_plugin = activity_to_plugin_map[
                    activity_node[1]["activity"].activity_type
                ]
                plugins_are_configured = self.are_plugins_configured(required_plugin)
                actions_are_supported = True

            except Exception as e:
                self._logger.exception(f"Caught plugin check error: {e}")
                plugins_are_configured = False
                actions_are_supported = False

        should_ack = plugins_are_configured and actions_are_supported

        self._logger.info(
            f"[mh] Should ack: {should_ack} | Plugins Configured: {plugins_are_configured}"
        )

        try:
            if should_ack:
                ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
                self._logger.debug("[recv activity] ACKED activity message.")
                self.check_activity_q.put(activity_node)
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, multiple=False)
                self._logger.debug("[recv activity] NACKED activity message.")
                # stuck in NACK loop; sleep helps alleviate what happens when
                #   a task can't get picked up by anyone (temporary).
                time.sleep(1)
        except Exception as e:
            self._logger.error(f"[mh] COULD NOT ACK! CAUGHT: {type(e).__name__}: {e}")

    def recv_activity(self):
        """Receive activity via RabbitMQ ACTIVITIES channel. Triggers _callback().
        """

        self._logger.info("[mh] Connecting to RabbitMQ RECV ACTIVITY broker...")

        # Here we use the queue factory to create queue object and listen on persistent listener.
        queue_client = self.queue_factory.create(QueueType.RABBITMQ, self.mq_args)
        queue_client.connect()

        queue_client.listen_and_do_callback(
            callback_func=self._callback,
            channel_to_listen="ACTIVITIES",
            should_auto_ack=False,
        )

    def send_activity_dag(self):
        """From RabbitMQ, send activities on RabbitMQ ACTIVITIES channel.
        """

        self._logger.info("[mh] Connecting to RabbitMQ SEND ACTIVITY broker...")
        queue_client = self.queue_factory.create(QueueType.RABBITMQ, self.mq_args)
        queue_client.connect()

        while True:
            self._logger.info("[send_activity] Waiting for messages...")
            activity_msg = self.msg_handler_send_activity_q.get()

            self._logger.info(f"[send_activity] Dispatching message: {activity_msg}...")
            try:
                queue_client.send(exchange="", channel="ACTIVITIES", body=activity_msg)
            except Exception as e:
                self._logger.error(
                    f"[mh] UNABLE TO SEND ACTIVITY MESSAGE! CAUGHT: {type(e).__name__}: {e}"
                )
            else:
                self._logger.debug("[send_activity] Successfully sent activity!")

    def recv_control(self):
        """Receive messages from the RabbitMQ CONTROL channel.
        """

        self._logger.info("[mh] Connecting to RabbitMQ RECV CONTROL broker...")
        queue_client = self.queue_factory.create(QueueType.RABBITMQ, self.mq_args)
        queue_client.connect()

        def callback(_1, _2, _3, body):
            control_msg = pickle.loads(body)
            self._logger.info(" [x recv_control] Received %r" % control_msg)
            self.recv_control_q.put(control_msg)

        queue_client.listen_and_do_callback(
            channel_to_listen="CONTROL", callback_func=callback, should_auto_ack=True
        )

    def send_control(self):
        """Continuously send control messages along the RabbitMQ CONTROL channel.
        """

        self._logger.info("[mh] Connecting to RabbitMQ SEND CONTROL broker...")
        queue_client = self.queue_factory.create(QueueType.RABBITMQ, self.mq_args)
        queue_client.connect()

        while True:
            self._logger.debug("[send_control] Waiting for messages...")
            activity_msg = self.msg_handler_send_control_q.get()

            self._logger.debug("[send_control] Message received! Sending...")
            try:
                queue_client.send(exchange="", channel="CONTROL", body=activity_msg)
            except Exception as e:
                self._logger.error(
                    f"[mh] COULD NOT SEND CONTROL MESSAGE! CAUGHT: {type(e).__name__}: {e}"
                )
            else:
                self._logger.info("[send_control] Successfully sent control message!")

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

        Parameters
        ----------
        plugin : str
            The name of a single plugin to try.
        cmd : str
            An argument that could be capably run by a given plugin
            (e.g., a Transfer plugin could 'auth').

        Returns
        -------
        bool
            Determines whether there were any errors in the plugin-checking process.
        """

        checked_result = self._settings.plugins.check(plugin_name=plugin, arguments=cmd)
        self._logger.debug(f"[mh] Checked result: {checked_result}")
        # return whether NO errors were detected.
        return not checked_result.error_detected()

    # TODO: feature add: -- are_plugins_configured AND necessary_actions_supported.
    def are_plugins_configured(self, plugin_label):
        """Check to see if plugins are configured.

        Parameters
        ----------
        plugin_label : str
            Name of plugin

        """
        self._logger.info(f"Checking to see if plugin---{plugin_label}---configured!")
        return self._settings.is_plugin_configured(plugin_label)

    def are_actions_supported(self, action_labels: list[str]):
        """Determine whether actions are supported.

        Parameters
        ----------
        action_labels: list[str]
            Labels of actions we want to check whether the plugins can process

        Returns
        -------
        bool
            Whether the actions are all supported

        Notes
        -----
        - Currently always returns 'TRUE' as actions are not implemented (just plugins).
        """
        self._logger.info(f"Action labels: {action_labels}")
        return True
