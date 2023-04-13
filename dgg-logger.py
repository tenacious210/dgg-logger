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

chat = DGGChat()
cloud_sync = True
log_name = "2000-12-31.txt"

if cloud_sync:
    storage_client = google.cloud.storage.Client()
    storage_bucket = storage_client.bucket("tenadev")
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()


def upload_logs(log_filename: str):
    if not os.path.exists(log_filename):
        logger.info(f"Couldn't find {log_filename} for upload")
        return
    blob = storage_bucket.blob(f"dgg-logs/{log_filename}")
    blob.upload_from_filename(log_filename)
    os.remove(log_filename)
    logger.info(f"Uploaded {log_filename}")


@chat.event()
def on_msg(msg: Message):
    global log_name
    msg_date = msg.timestamp.strftime("%Y-%m-%d")
    if not log_name == f"{msg_date}.txt":
        if cloud_sync:
            Thread(target=upload_logs, args=[log_name]).start()
        log_name = f"{msg_date}.txt"
    log_time = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    log = f"[{log_time} UTC] {msg.nick}: {msg.data}"
    with open(log_name, "a") as log_txt:
        log_txt.write(f"{log}\n")


if __name__ == "__main__":
    chat.run_forever(sleep=0)
