from datetime import datetime
from threading import Thread
import logging
import sys
import os
from dggbot import DGGChat, Message
import google.cloud.storage
import google.cloud.logging


logging.getLogger("websocket").setLevel(logging.CRITICAL)
logging.root.disabled = True
logger = logging.getLogger("dgg-logger")
logger.addHandler(logging.StreamHandler(sys.stdout))
formatter = logging.Formatter("%(name)s: %(message)s")
for handler in logger.handlers:
    handler.setFormatter(formatter)
logger.setLevel(logging.INFO)


class DGGLogger(DGGChat):
    cloud_sync = False

    def __init__(self):
        super().__init__()
        self.logfile = "2000-12-31.txt"
        if self.cloud_sync:
            storage_client = google.cloud.storage.Client()
            self.storage_bucket = storage_client.bucket("tenadev")
            logging_client = google.cloud.logging.Client()
            logging_client.setup_logging()

    def on_msg(self, msg: Message):
        super().on_msg(msg)
        msg_datetime = datetime.utcfromtimestamp(float(msg.timestamp / 1000))
        msg_date = msg_datetime.strftime("%Y-%m-%d")
        if not self.logfile == f"{msg_date}.txt":
            if self.cloud_sync:
                Thread(target=self.upload_logs, args=[self.logfile.name]).start()
            self.logfile = f"{msg_date}.txt"
        log_time = msg_datetime.strftime("%Y-%m-%d %H:%M:%S")
        log = f"[{log_time} UTC] {msg.nick}: {msg.data}"
        with open(self.logfile, "a") as logfile:
            logfile.write(f"{log}\n")

    def on_quit(self, msg: Message):
        if msg.nick.lower() in self._users.keys():
            del self._users[msg.nick.lower()]
        for func in self._events.get("on_quit", tuple()):
            func(msg)

    def run(self, origin: str = None):
        while True:
            logger.info("Starting DGG logger")
            self.ws.run_forever(origin=origin or self.URL)

    def upload_logs(self, log_filename: str):
        if not os.path.exists(log_filename):
            logger.info(f"Couldn't find {log_filename} for upload")
            return
        blob = self.storage_bucket.blob(f"dgg-logs/{log_filename}")
        blob.upload_from_filename(log_filename)
        os.remove(log_filename)
        logger.info(f"Uploaded {log_filename}")


if __name__ == "__main__":
    dgg_logger = DGGLogger()
    dgg_logger.run()
