
import pickle
import pika
import threading
import time
import zmq

from queue import Queue

from zambeze.orchestration.db.model.activity_model import ActivityModel
from zambeze.orchestration.db.dao.activity_dao import ActivityDAO


class MessageHandler(threading.Thread):
    def __init__(self, agent_id, settings, logger):
        threading.Thread.__init__(self)
        self.agent_id = agent_id
        self._settings = settings
        self._logger = logger

        # RabbitMQ stuff  # TODO: move to josh's queue service abstraction.
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(self._settings.settings["rmq"]["host"]))
        self._logger.info("[Message Handler] Creating RabbitMQ channels...")
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='ACTIVITIES')
        self.channel.queue_declare(queue='CONTROL')  # TODO: back-to-back queue declares.
        self._logger.info("[Message Handler] RabbitMQ broker and channel both created successfully!")

        self._activity_dao = ActivityDAO(self._logger)

        self._zmq_context = zmq.Context()
        self._zmq_socket = self._zmq_context.socket(zmq.REP)
        self._logger.info(f"[Message Handler] Binding to ZMQ: {self._settings.get_zmq_connection_uri()}")
        self._zmq_socket.bind(self._settings.get_zmq_connection_uri())

        # Queues to allow safe inter-thread communication.
        self.send_activity_q = Queue()
        self.check_activity_q = Queue()
        self.send_control_q = Queue()
        self._recv_control_q = Queue()

        self._logger.info("[Message Handler] Message handler successfully initialized!")

        # THREAD 1: recv activities from campaign
        campaign_listener = threading.Thread(target=self.recv_activities_from_campaign, args=())
        # THREAD 2: recv activities from rmq
        activity_listener = threading.Thread(target=self.recv_activity, args=())
        # THREAD 3: recv control from RMQ
        control_listener = threading.Thread(target=self.recv_control, args=())
        # THREAD 4: send activity to RMQ
        activity_sender = threading.Thread(target=self.send_activity, args=())

        # self.threads = [campaign_listener, activity_listener, control_liste]

        # def run(self):
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
            self._logger.info("[recv_activities_from_campaign] Waiting for messages from campaign...")

            # Use ZMQ to receive activities from campaign.
            activity_message = self._zmq_socket.recv()
            self._logger.debug(f"[recv_activities_from_campaign] Received message from campaign: {activity_message}")

            activity = ActivityModel(
                agent_id=str(self.agent_id), created_at=int(time.time() * 1000)
            )
            self._logger.debug(f"[recv_activities_from_campaign] Creating activity in the DB: {activity}")
            self._activity_dao.insert(activity)
            self._logger.debug("[recv_activities_from_campaign] Saved in the DB!")

            self.send_activity_q.put(activity_message)

    def recv_activity(self):
        """
        >> Async

        Get activity from 'ACTIVITIES' queue.
        If we have the correct plugins, then we keep it (ack). Otherwise, we put it back (nack).
        """

        self._logger.info(f"[Message Handler] Connecting to RabbitMQ RECV ACTIVITY broker...")
        recv_activities_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        recv_activities_channel = recv_activities_connection.channel()

        self._logger.info(f"[recv_activity] receiving activity...")

        def callback(ch, method, properties, body):
            activity = pickle.loads(body)
            self._logger.debug(" [x recv_activity] Received %r" % activity)
            self.check_activity_q.put(activity)  # TODO check that this is doing anything.
            parseable_activity = activity.generate_message()
            self._logger.debug(f"PARSEABLE ACTIVITY: {parseable_activity}")
            # TODO: should be able to require a list of plugins (not just one).
            # TODO: move these to agent-init.
            plugins_are_configured = self.are_plugins_configured(parseable_activity['plugin'])
            plugins_are_ready = self.can_plugins_run(parseable_activity['plugin'], cmd=parseable_activity['cmd'])

            should_ack = plugins_are_configured and plugins_are_ready

            # TODO: additional functionalities
            # 1. Pulling down messages based on metadata filters rather than pulling down anything.
            # 2. Initial 'broadcast' check to see if there is a single agent capable of running each activity?
            # 3. Agent thinks it can run activity. Hits some sort of failure case (either in execution or configuration)
            #   ... wrap this up as a new Error-flag activity, and let it be handled accordingly.
            # ROUTING: https://www.rabbitmq.com/tutorials/tutorial-four-python.html

            self._logger.debug(f"Should ack: {should_ack} | Plugins Configured: {plugins_are_configured} | "
                               f"Plugins Ready: {plugins_are_ready}")
            try:
                if should_ack:
                    recv_activities_channel.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
                    self._logger.debug("[recv activity] ACKED message.")
                else:
                    recv_activities_channel.basic_nack(delivery_tag=method.delivery_tag, multiple=False)
                    self._logger.debug("[recv activity] NACKED message.")
                    # stuck in NACK loop.
                    time.sleep(1)   # TODO !!!!!!!!!!!!!
            except Exception as e:
                self._logger.error(f"[Message Handler] CAUGHT: {e}")

        recv_activities_channel.basic_consume(queue='ACTIVITIES', on_message_callback=callback, auto_ack=False)

        self._logger.debug(' [*] Waiting for ACTIVITY messages. To exit press CTRL+C')
        # TODO: Death condition.
        recv_activities_channel.start_consuming()

    def send_activity(self):
        """
        (from agent.py) input activity; send to "ACTIVITIES" queue.
        """

        self._logger.info(f"[Message Handler] Connecting to RabbitMQ SEND ACTIVITY broker...")
        send_activities_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        send_activities_channel = send_activities_connection.channel()

        while True:
            self._logger.info(f"[send_activity] Waiting for messages...")
            activity_msg = self.send_activity_q.get()

            self._logger.info(f"[activity structure] {activity_msg}")

            self._logger.info(f"[send_activity] Message received! Sending...")
            try:
                send_activities_channel.basic_publish(exchange='',
                                                      routing_key='ACTIVITIES',
                                                      body=activity_msg)
            except Exception as e:
                self._logger.error(f"CAUGHT: {e}")
            self._logger.debug(f"[send_activity] Successfully sent activity!")

    def recv_control(self):
        """
        Receive messages from the control channel!
        """

        self._logger.info(f"[Message Handler] Connecting to RabbitMQ RECV CONTROL broker...")
        recv_control_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        recv_control_channel = recv_control_connection.channel()

        self._logger.info(f"[recv_control] receiving activity...")

        def callback(ch, method, properties, body):
            activity = pickle.loads(body)
            self._logger.info(" [x recv_activity] Received %r" % activity)
            self._recv_control_q.put(activity)

        recv_control_channel.basic_consume(queue='CONTROL', on_message_callback=callback, auto_ack=True)

        self._logger.info(' [*] Waiting for messages. To exit press CTRL+C')
        # TODO: Death condition.
        recv_control_channel.start_consuming()

    def send_control(self):
        """
        (from agent.py) input control message; send to "CONTROL" queue.
        """

        self._logger.info(f"[Message Handler] Connecting to RabbitMQ SEND CONTROL broker...")
        send_control_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        send_control_channel = send_control_connection.channel()

        while True:
            self._logger.debug(f"[send_activity] Waiting for messages...")
            activity_msg = self.send_activity_q.get()

            self._logger.debug(f"[send_activity] Message received! Sending...")
            try:
                send_control_channel.basic_publish(exchange='',
                                                      routing_key='CONTROL',
                                                      body=activity_msg)
            except Exception as e:
                self._logger.info(f"Caught error: {e}")
            self._logger.info(f"[send_activity] Successfully sent activity!")

    def can_plugins_run(self, plugin, cmd):

        # Running Checks
        # Returned results should be double nested dict with a tuple of
        # the form
        #
        # "plugin": { "action": (bool, message) }
        #
        # The bool is a true or false which indicates if the action
        # for the plugin is a problem, the message is an error message
        # or a success statement

        checked_result = self._settings.plugins.check(plugin_name=plugin, arguments=cmd)
        self._logger.debug(f"Checked result: {checked_result}")
        # return whether NO errors were detected.
        return not checked_result.errorDetected()

    def are_plugins_configured(self, plugin_label):
        return self._settings.is_plugin_configured(plugin_label)

