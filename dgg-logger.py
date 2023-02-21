from threading import Thread
import logging
import os

from dggbot import DGGChat, Message
import google.cloud.storage
import google.cloud.logging


logging.getLogger("websocket").setLevel(logging.CRITICAL)
logging.root.disabled = True
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DGGLogger(DGGChat):
    cloud_sync = True

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
        msg_date = msg.timestamp.strftime("%Y-%m-%d")
        if not self.logfile == f"{msg_date}.txt":
            if self.cloud_sync:
                Thread(target=self.upload_logs, args=[self.logfile]).start()
            self.logfile = f"{msg_date}.txt"
        log_time = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        log = f"[{log_time} UTC] {msg.nick}: {msg.data}"
        with open(self.logfile, "a") as logfile:
            logfile.write(f"{log}\n")

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
    dgg_logger.run_forever(sleep=0)
