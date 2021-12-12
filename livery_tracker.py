import config
from model import model
import requests
import os
import json
import datetime
import time
import traceback

model.open_model()


def generate_notification_messages_for_discord(action_id: int) -> list[str]:
    """
    We have to consider a few cases:
    1. Item added
    2. Item deleted
    3. For existing item one of the prices was changed
    """

    messages: list = []

    new_entries = model.get_diff_action_id(action_id)
    for entry in new_entries:
        if entry['Old Name'] == 'New Item':  # it is new item in the story
            message = f"""```
New item: {entry['New Name']}
\tcurrent price: {entry['New Current Price']}
\torig price: {entry['New Original Price']}
```
link to item image: {entry['URL to image']}
details about this change: <https://livery.demb.design/diff/{action_id}>"""
            messages.append(message)

        elif entry['New Name'] == 'Deleted Item':  # it is deleted from the store item
            message = f"""```
Item removed: {entry['Old Name']}
Last known prices:
\tcurrent price: {entry['Old Current Price']}
\torig_price: {entry['Old Original Price']}
```
link to item image: {entry['URL to image']}
details about this change: <https://livery.demb.design/diff/{action_id}>"""
            messages.append(message)

        elif (
                entry['New Original Price'] != entry['Old Original Price'] or
                entry['New Current Price'] != entry['Old Current Price']
        ):  # it is item with changed price
            message = f"""```
Change price for known item: {entry['New Name']}
\tcurrent price: {entry['Old Current Price']} -> {entry['New Current Price']}
\torig price: {entry['Old Original Price']} -> {entry['New Original Price']}
```
link to item image: {entry['URL to image']}
details about this change: <https://livery.demb.design/diff/{action_id}>"""
            messages.append(message)

    return messages


class NotifyDiscord:
    def __init__(self, webhooks: list[str]):
        """
        Takes list of webhooks urls to send
        """

        self.webhooks: list[dict] = []
        for webhook in webhooks:
            webhook_dict = {'url': webhook, 'last_send': 0}
            self.webhooks.append(webhook_dict)

    def send(self, messages_list: list[str]) -> None:
        for one_message in messages_list:
            for _webhook_dict in self.webhooks:
                self._send_one_webhook(one_message, _webhook_dict)

    def _send_one_webhook(self, _message: str, _webhook_dict: dict) -> None:
        while not _webhook_dict['last_send'] + 5 < time.time():
            pass  # I don't trust to time.sleep()

        try:
            r = requests.post(
                _webhook_dict['url'],
                data=f'content={requests.utils.quote(_message)}',
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            _webhook_dict['last_send'] = time.time()  # shallow copy

            r.raise_for_status()

        except Exception:
            print(f'Fail on sending message {_message!r} to {_webhook_dict["url"]!r}')
            print(traceback.format_exc())


def get_onlinestore_data() -> list[dict]:
    items = list()
    for item in requests.get("https://api.zaonce.net/3.0/store/product").json():
        items.append(dict(name=item["title"], cur_price=item["current_price"], orig_price=item["original_price"],
                          image=item["image"]))
    # print(f"Got {len(items)} items")
    return items


def history_insert() -> None:
    for file in sorted(os.listdir('history')):
        with open('history\\' + file, 'r') as open_file:
            content = json.load(open_file)
            if 'image' not in content[0].keys():
                for item in content:
                    item['image'] = ''

            timestamp = datetime.datetime.utcfromtimestamp(int(file.split('.')[0])).strftime('%Y-%m-%dT%H:%M:%SZ')
            for item in content:
                item['timestamp'] = timestamp

            model.insert_livery_timestamp(content)


discord_sender = NotifyDiscord(config.discord_webhooks)

action_id_to_check: int = model.insert_livery(get_onlinestore_data())
discord_sender.send(generate_notification_messages_for_discord(action_id_to_check))

model.close_model()
