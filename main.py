from threading import Thread
import logging
import os
import sys

from dggbot import DGGChat, Message
import google.cloud.storage

logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)

sys.tracebacklimit = 0
logging.basicConfig(level=logging.INFO)
logging.getLogger("websocket").disabled = True
logging.getLogger("dgg-bot").disabled = True

chat = DGGChat()
# Set cloud_sync to False to run locally.
# Set to true and create a dummy file called 2000-12-31.txt to test Google Cloud connectivity.
cloud_sync = True
log_name = os.path.join(logs_dir, "2000-12-31.txt")

if cloud_sync:
    storage_client = google.cloud.storage.Client(project="tenacious210")
    storage_bucket = storage_client.bucket("tenadev")


def upload_logs(log_filename: str):
    if not os.path.exists(log_filename):
        logging.info(f"Couldn't find {log_filename} for upload")
        return
    blob = storage_bucket.blob(f"dgg-logs/{os.path.basename(log_filename)}")
    blob.upload_from_filename(log_filename)
    os.remove(log_filename)
    logging.info(f"Uploaded {log_filename}")


@chat.event()
def on_msg(msg: Message):
    global log_name
    msg_date = msg.timestamp.strftime("%Y-%m-%d")
    new_log_name = os.path.join(logs_dir, f"{msg_date}.txt")
    if not log_name == new_log_name:
        if cloud_sync:
            Thread(target=upload_logs, args=[log_name]).start()
        log_name = new_log_name
    log_time = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    log = f"[{log_time} UTC] {msg.nick}: {msg.data}"
    with open(log_name, "a") as log_txt:
        log_txt.write(f"{log}\n")


if __name__ == "__main__":
    chat.run_forever(sleep=0)
