import threading

from time import time
from queue import Queue


class Monitor(threading.Thread):
    def __init__(self, dag_msg, logger):
        threading.Thread.__init__(self)
        self.to_monitor_q = Queue()
        self.to_status_q = Queue()
        self.completed = False

        # Now we want to hold (and periodically log) until all subtasks are complete.
        self.dag_dict = dict()
        self.dag_msg = dag_msg

        self.monitor_hb_s = 5

        self._logger = logger

    def run(self):
        """Override the Thread 'run' method to instead run our
        process when Thread.start() is called!"""

        self._logger.info("[MONITOR] ping from monitor.py thread! ")
        # Add all activities (besides the monitor) to our dict.
        for activity_id in self.dag_msg[1]["all_activity_ids"]:
            if activity_id == "MONITOR":
                continue
            self.dag_dict[activity_id] = "PROCESSING"
            self._logger.info("[monitor] Marked all campaign activities for monitoring!")

        last_hb_time = time()
        while True:
            # Quick check to see if all values are NOT "PROCESSING"
            proc_count = sum(x == "PROCESSING" for x in self.dag_dict.values())

            # self._logger.info("[monitor] RRR")
            if proc_count == 0:
                self.completed = True

            # self._logger.info("[monitor] SSS")

            if self.to_monitor_q.qsize() > 0:
                status_msg = self.to_monitor_q.get()
                self._logger.info("[monitor] TTT")
                self._logger.info("[monitor] RECEIVED CONTROL MESSAGE!")
                self._logger.info(f"[monitor] {status_msg}")
                if status_msg.activity_id in self.dag_dict:
                    status = status_msg["status"]
                    self.dag_dict[status_msg["activity_id"]] = status

            # If enough time has passed, hb...
            if time() - last_hb_time > self.monitor_hb_s:

                self._logger.info(f"Foobar: {self.dag_msg}")

                # Send heartbeat and sleep.
                hb_monitor_msg = {
                        'status': "MONITORING",
                        'activity_id': "MONITORING",
                        'campaign_id': self.dag_msg[1]["campaign_id"],
                        'msg': 'simple heartbeat notification.'
                    }

                self.to_status_q.put(hb_monitor_msg)
                self._logger.info("[monitor] Enqueued monitor hb message! ")
                last_hb_time = time()

            # TODO: IF EVERYTHING IS DONE, TERMINATE BY SETTING EXECUTOR.MONITOR TO "NONE".
