from google.cloud import storage
from dggbot import DGGChat, Message
from logging.handlers import TimedRotatingFileHandler
import logging
from time import tzname
import sys
from schedule import repeat, every, run_pending
from datetime import datetime, timedelta
import os
from time import sleep
from threading import Thread

dgg_client = DGGChat()
storage_client = storage.Client()
storage_bucket = storage_client.bucket("tenadev")


@dgg_client.event()
def on_msg(msg: Message):
    file_logger.info(f"{msg.nick}: {msg.data}")


@repeat(every().day.at("00:01"))
def upload_logs():
    yesterday = datetime.now() - timedelta(days=1)
    blob = None
    for file in os.listdir():
        if ".log" in file:
            with open(file, "r") as log:
                first_line = log.readline()
            log_date = first_line[1 : first_line.find(" ")]
            if datetime.strptime(log_date, "%Y-%m-%d").date() == yesterday.date():
                blob = storage_bucket.blob(f"dgg-logs/{log_date}.txt")
                blob.upload_from_filename(file)
                return
    if not blob:
        main_logger.warning("Couldn't upload log file")


def upload_logs_thread():
    while True:
        run_pending()
        sleep(30)


logging.getLogger("websocket").setLevel(logging.CRITICAL)
logging.root.disabled = True

log_format = f"[%(asctime)s {tzname[0]}] %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"
log_formatter = logging.Formatter(log_format, datefmt=date_format)

file_logger = logging.getLogger("dgg-file-logger")
file_handler = TimedRotatingFileHandler(
    filename="dgg-logs.log",
    when="D",
    interval=1,
    backupCount=3650,
    utc=True,
)
file_handler.setFormatter(log_formatter)
file_logger.addHandler(file_handler)
file_logger.setLevel(logging.INFO)
file_logger.propagate = False

main_logger = logging.getLogger(__name__)
main_handler = logging.StreamHandler(sys.stdout)
main_handler.setFormatter(log_formatter)
main_logger.addHandler(main_handler)
main_logger.setLevel(logging.INFO)


if __name__ == "__main__":
    upload_thread = Thread(target=upload_logs_thread)
    upload_thread.start()
    while True:
        main_logger.info("Starting DGG client")
        dgg_client.run()
