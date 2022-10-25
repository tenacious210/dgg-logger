from google.cloud import storage
import google.cloud.logging
from dggbot import DGGChat, Message
from datetime import datetime
import asyncio
import logging
import os
import sys

dgg_client = DGGChat()
current_date = "2000-12-31"
cloud_sync = True

logging.getLogger("websocket").setLevel(logging.CRITICAL)
logging.root.disabled = True
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.propagate = False
if cloud_sync:
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()


@dgg_client.event()
def on_msg(msg: Message):
    global current_date
    msg_datetime = datetime.utcfromtimestamp(float(msg.timestamp / 1000))
    msg_date = msg_datetime.strftime("%Y-%m-%d")
    log_time = msg_datetime.strftime("%Y-%m-%d %H:%M:%S")
    log = f"[{log_time} UTC] {msg.nick}: {msg.data}"
    with open(f"{msg_date}.txt", "a") as logfile:
        logfile.write(f"{log}\n")
    if msg_date != current_date and cloud_sync:
        old_logfile = f"{current_date}.txt"
        if os.path.exists(old_logfile):
            asyncio.create_task(upload_logs(old_logfile))
        else:
            logger.info(f"Couldn't find {old_logfile}")
        current_date = msg_date


async def upload_logs(log_filename: str):
    storage_client = storage.Client()
    storage_bucket = storage_client.bucket("tenadev")
    blob = storage_bucket.blob(f"dgg-logs/{log_filename}")
    blob.upload_from_filename(log_filename)
    os.remove(log_filename)
    logger.info(f"Uploaded {log_filename}")


def main():
    while True:
        logger.info("Starting DGG logger")
        dgg_client.run()


if __name__ == "__main__":
    main()
