#!/usr/bin/python3
"""
It is old version of livery_tracker, bugged in alerting part
"""
import json
import logging
import queue
import sys
import threading
import time

import requests

# Dump new raw jsons?
DUMP = True

url = ""  # DEMB
url2 = ""  # KISQ
# url = ""  # DEV
# url2 = ""  # DEV 2

# setting up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stdout_handler)

localdb_file = "local_storage.json"
images_base_url = "https://dlc.elitedangerous.com/images/med/"


class Messages_sender(threading.Thread):
    """Sending message to discord asynchronously"""

    def __init__(self, url, messages_queue=queue.Queue()):
        threading.Thread.__init__(self)
        self.queue = messages_queue
        self.url = url
        self.headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    def put(self, message):  # put message into queue
        self.queue.put(message)

    def exit(self, lock=False):  # stop messages_sender thread
        self.queue.put('exit')
        if lock:
            self.join()

    def run(self):
        isStopped = False
        while True:
            if isStopped:
                logger.debug("Got exit message")
                break

            message_from_queue = self.queue.get()

            if message_from_queue == "exit":
                logger.debug("Got exit message")
                break

            message = requests.utils.quote(message_from_queue)

            try:
                while True:
                    logger.debug('===BEGIN OF MESSAGE DUMP===\n' + str(
                        f"content={message}".encode('utf-8')) + '\n===END OF MESSAGE DUMP===')
                    r = requests.post(self.url, data=f"content={message}".encode('utf-8'), headers=self.headers)

                    if r.status_code == 204:  # If success
                        logger.debug("Successful sent, status code: " + str({r.status_code}) + ", text: " + r.text)
                        time.sleep(1)
                        break

                    if r.status_code == 429:
                        # We are rate limited, see https://discord.com/developers/docs/topics/rate-limits
                        retry_after = int(r.headers["retry-after"]) / 1000
                        retry_time = time.time() + retry_after
                        logger.debug(
                            f"We are rate limited, text: {r.text}\n Will retry after {int(retry_time - time.time())}")

                        while time.time() < retry_time:
                            time.sleep(retry_after)

                        continue

                    if r.status_code != 204:  # Any others cases
                        logger.error(f"Status code: {r.status_code}! {r.text}\nMessage: {message}")
                        break

            except Exception as e:
                logger.warning(f"Got exception in sender thread\n{e}")


# setting up messages sender
messages_sender = Messages_sender(url)
messages_sender.start()

messages_sender2 = Messages_sender(url2)
messages_sender2.start()

# def get_onlinestore_data():
#    with open("store_sample.json") as store_sample:
#        items = list()
#        for item in json.load(store_sample):
#            items.append({"name": item["title"], "cur_price": item["current_price"], "orig_price": item["original_price"]})
#        return items


def on_exit():
    try:
        with open(localdb_file, "w") as dbfile:
            dbfile.write(json.dumps(online_items))
    except Exception as e:
        logger.error("Got exception on_exit() on file saving:\n" + str(e))
    logger.debug("Waiting for sender thread")
    messages_sender.exit(lock=True)
    messages_sender2.exit(lock=True)
    exit()


def get_onlinestore_data():
    logger.debug("Getting online store data")
    items = list()
    for item in json.loads(requests.get("https://api.zaonce.net/3.0/store/product").text):
        items.append(dict(name=item["title"], cur_price=item["current_price"], orig_price=item["original_price"],
                          image=item["image"]))
    logger.debug(f"Got {len(items)} items")
    return items


def get_localstore_data():
    logger.debug("Getting local data")
    try:
        with open(localdb_file) as local:
            data = json.load(local)
            logger.debug(f"Found local data file with {len(data)} items")
            return data
    except FileNotFoundError:
        logger.debug("Didn't found local data file")
        return None


online_items = get_onlinestore_data()
local_items = get_localstore_data()

if local_items is None:
    logger.info("No local data file, creating new one")
    on_exit()

if str(online_items) != str(local_items):
    logger.debug("Different data")
    if DUMP:
        logger.debug("DUMP is True, dumping raw json")
        with open(f"{int(time.time())}.json", "w") as file:
            file.write(json.dumps(online_items))
else:
    logger.debug("No new data, exiting")
    on_exit()

for online_item in online_items:
    if online_item not in local_items:  # updated or even new item in store
        logger.debug(f"Updated or even new item in store: {online_item}")

        online_item_name = online_item[
            "name"]  # lets try to find item with this name in local db but with different price

        for local_item in local_items:
            local_item_name = local_item["name"]

            if online_item_name == local_item_name:  # updated price for existing item
                logger.debug(f"Found this item with different price: {local_item}")
                local_item_cur_price = local_item["cur_price"]
                local_item_orig_price = local_item["orig_price"]

                online_item_item_cur_price = online_item["cur_price"]
                online_item_item_orig_price = online_item["orig_price"]

                image_url = images_base_url + online_item["image"]

                message = f"```Change price for known item: {online_item_name}\n\tcurrent price: {local_item_cur_price} -> {online_item_item_cur_price}\n\torig price: {local_item_orig_price} -> {online_item_item_orig_price}\n```\nlink to item image: {image_url}"
                messages_sender.put(message)
                messages_sender2.put(message)
                local_items.remove(local_item)
                find = True
                break
        else:  # new item in store. Works if we didn't break line in for
            image_url = images_base_url + online_item["image"]
            message = f"```New item: {online_item['name']}\n\tcurrent price: {online_item['cur_price']}\n\torig price: {online_item['orig_price']}\n```\nlink to item image: {image_url}"
            messages_sender.put(message)
            messages_sender2.put(message)
            continue

        if find:
            continue

    local_items.remove(online_item)

for removed_item in local_items:  # Detecting removed items from store
    message = f"```Item removed: {removed_item['name']}\nLast known prices:\n\tcurrent price: {removed_item['cur_price']}\n\torig_price: {removed_item['orig_price']}```"
    messages_sender.put(message)
    messages_sender2.put(message)

on_exit()

"""
livery_tracker.service
[Unit]
Description=track frontier livery store for ED
After=syslog.target
After=network.target

[Service]
Type=oneshot
User=user2
WorkingDirectory=/home/user2/livery_tracker
ExecStart=/home/user2/livery_tracker/livery_tracker.py

[Install]
WantedBy=multi-user.target

livery_tracker.timer
[Unit]
Description=run livery_tracker

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=multi-user.target
"""
