from model import model
import requests
import os
import json
import datetime

model.open_model()


def get_onlinestore_data() -> list[dict]:
    items = list()
    for item in requests.get("https://api.zaonce.net/3.0/store/product").json():
        items.append(dict(name=item["title"], cur_price=item["current_price"], orig_price=item["original_price"],
                          image=item["image"]))
    print(f"Got {len(items)} items")
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


model.insert_livery(get_onlinestore_data())

model.close_model()
