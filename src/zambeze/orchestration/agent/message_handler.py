import pickle
import threading
import time
import zmq

from queue import Queue
from zambeze.orchestration.db.model.activity_model import ActivityModel
from zambeze.orchestration.db.dao.activity_dao import ActivityDAO
from zambeze.orchestration.queue.queue_rmq import QueueRMQ
from zambeze.campaign.dag import DAG

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
        # TODO: bring back.
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
        """
        >> Async

        Receives message from campaign on ZMQ socket, saves in send_activity_q
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

    # Custom RabbitMQ callback; made decision to put here so that we can access the messages.
    def _callback(self, ch, method, _properties, body):
        self._logger.debug("uno")
        self._logger.debug(
            "[mh-recv-activity] Processing callback function for activity queue recv."
        )
        activity_node = DAG.deserialize_node(body)
        self._logger.info(f"[mn-recv-activity] receiving activity...{activity_node}")

        plugins_are_configured = False
        actions_are_supported = False

        # Anyone can monitor or terminate.
        self._logger.debug("dos")

        if activity_node[0] in ["MONITOR", "TERMINATOR"]:
            self._logger.debug("tres")
            plugins_are_configured = True
            actions_are_supported = True
            self._logger.info(
                f"[mh] Zambeze activity received of ID: {activity_node[0]}"
            )

        else:
            self._logger.debug("quatro")
            try:
                self._logger.info("[mh] Unpacking activity info from queue...")
            except Exception as e:
                self._logger.error(e)

            self._logger.debug("cinco")

            # TODO: TYLER THIS IS CAUSING PROBLEM
            # I THINK I NEED TO MAXIMIZE
            try:
                required_plugin = activity_to_plugin_map[
                    activity_node[1]["activity"].type.upper()
                ]
            except Exception as e:
                self._logger.exception(f"Caught-a-lot: {e}")
            self._logger.debug("ses")
            plugins_are_configured = self.are_plugins_configured(required_plugin)
            actions_are_supported = (
                True  # self.are_actions_supported(action_labels=[""])
            )

        self._logger.debug("siete")
        should_ack = plugins_are_configured and actions_are_supported

        self._logger.info(
            f"[mh] Should ack: {should_ack} | Plugins Configured: {plugins_are_configured}"
        )

        self._logger.debug("ocho")

        try:
            if should_ack:
                ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
                self._logger.debug("[recv activity] ACKED activity message.")
                self.check_activity_q.put(activity_node)
                self._logger.debug("nueve")
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, multiple=False)
                self._logger.debug("[recv activity] NACKED activity message.")
                # stuck in NACK loop; sleep helps alleviate what happens when
                #   a task can't get picked up by anyone (temporary).
                self._logger.debug("dies")
                time.sleep(1)
        except Exception as e:
            self._logger.error(f"[mh] COULD NOT ACK! CAUGHT: {type(e).__name__}: {e}")

    def recv_activity(self):
        """
        >> Async

        Get activity from 'ACTIVITIES' queue.
        If we have the correct plugins, then we keep it (ack). Otherwise, we
        put it back (nack).
        """
        self._logger.info("[mh] Connecting to RabbitMQ RECV ACTIVITY broker...")

        # Here we use the queue factory to create queue object and listen on persistent listener.
        queue_client = QueueRMQ(self.mq_args, logger=self._logger)
        queue_client.connect()

        queue_client.listen_and_do_callback(
            callback_func=self._callback,
            channel_to_listen="ACTIVITIES",
            should_auto_ack=False,
        )

    def send_activity_dag(self):
        """
        (from agent.py) input activity; send to "ACTIVITIES" queue.
        """
        self._logger.info("[mh] Connecting to RabbitMQ SEND ACTIVITY broker...")

        queue_client = QueueRMQ(self.mq_args, logger=self._logger)
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
        """
        Receive messages from the control channel!
        """
        self._logger.info("[mh] Connecting to RabbitMQ RECV CONTROL broker...")

        queue_client = QueueRMQ(self.mq_args, logger=self._logger)
        queue_client.connect()

        def callback(_1, _2, _3, body):
            control_msg = pickle.loads(body)
            self._logger.info(" [x recv_control] Received %r" % control_msg)
            self.recv_control_q.put(control_msg)

        queue_client.listen_and_do_callback(
            channel_to_listen="CONTROL", callback_func=callback, should_auto_ack=True
        )

    def send_control(self):
        """
        (from agent.py) input control message; send to "CONTROL" queue.
        """
        self._logger.info("[mh] Connecting to RabbitMQ SEND CONTROL broker...")

        queue_client = QueueRMQ(self.mq_args, logger=self._logger)
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
        """

        checked_result = self._settings.plugins.check(plugin_name=plugin, arguments=cmd)
        self._logger.debug(f"[mh] Checked result: {checked_result}")
        # return whether NO errors were detected.
        return not checked_result.error_detected()

    # TODO: feature add: -- are_plugins_configured AND necessary_actions_supported.
    def are_plugins_configured(self, plugin_label):
        return self._settings.is_plugin_configured(plugin_label)

    def are_actions_supported(self, action_labels: list[str]):
        self._logger(f"Action labels: {action_labels}")
        """ TODO: Should potentially return false once we do action checking. """
        return True
