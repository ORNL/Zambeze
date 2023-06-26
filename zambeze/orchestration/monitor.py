
import threading

from queue import Queue


class Monitor(threading.Thread):
    def __init__(self, dag_msg, logger):
        threading.Thread.__init__(self)
        self.to_monitor_q = Queue()
        self.completed = False

        # Now we want to hold (and periodically log) until all subtasks are complete.
        self.dag_dict = dict()
        self.dag_msg = dag_msg

        self._logger = logger

    def run(self):
        """Override the Thread 'run' method to instead run our
        process when Thread.start() is called!"""
        # Create persisent "__process()"
        # self.__process()

        self._logger.info("[MONITOR] ping from monitor.py thread! ")
        # Add all activities (besides the monitor) to our dict.
        for activity_id in self.dag_msg[1]["all_activity_ids"]:
            if activity_id == "MONITOR":
                continue
            self.dag_dict[activity_id] = "PROCESSING"

        while True:
            # Quick check to see if all values are NOT "PROCESSING"
            proc_count = sum(x == 'PROCESSING' for x in self.dag_dict.values())

            if proc_count == 0:
                self.completed = True

            status_msg = self.to_monitor_q.get()
            if status_msg.activity_id in self.dag_dict:
                status = status_msg["status"]
                self.dag_dict[status_msg['activity_id']] = status
