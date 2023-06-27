import threading

from time import time, sleep
from queue import Queue


class Monitor(threading.Thread):
    def __init__(self, dag_msg, logger):
        threading.Thread.__init__(self)

        self.dag_msg = dag_msg
        self._logger = logger
        self.monitor_hb_s = 5  # seconds between heartbeats.

        # Internal queues.
        self.to_monitor_q = Queue()
        self.to_status_q = Queue()

        # Now we want to hold (and periodically log) until all subtasks are complete.
        self.dag_dict = dict()

        # So executor can check if we need to spin down monitor.
        self.completed = False

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
            self._logger.info(f"Current proc count: {proc_count}")
            self._logger.info(f"Dag dict: {self.dag_dict}")

            if proc_count == 0:
                self.completed = True
                self._logger.info(f"[monitor] Final campaign statuses: {self.dag_dict}")
                # break
                # Bit of a wacky (but harmless hack) bc monitor doesn't need to do anything, but
                # ... needs to wait until it is shut down by executor.
                sleep(10)

            if self.to_monitor_q.qsize() > 0:
                status_msg = self.to_monitor_q.get()

                self._logger.info("[monitor] RECEIVED CONTROL MESSAGE!")
                self._logger.info(f"[monitor-status] {status_msg}")

                if status_msg == "KILL":
                    self._logger.info("[monitor] Healthy KILL signal received. Tearing down...")
                    break

                if status_msg["activity_id"] in self.dag_dict:
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
