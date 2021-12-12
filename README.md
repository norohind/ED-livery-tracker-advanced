# What it is?
It is software aimed to track assortment in livery store of game Elite: Dangerous by Frontier Developments. It tracks appearing new items, deleting items, price changes.
Project stores its data in postgres DB and consists of two parts:
1. Web part `web.py` - intended for inspecting historical changes. You can find a live instance at https://livery.demb.design/livery.
2. Updater part `livery_tracker.py` - requests livery store content and insert it to DB. Updater part also performs send notification to discord by webhook, you can use multiple webhooks.

# How to run
## Updater
In order to run updater you have to set some env variables and execute `livery_tracker.py` periodically. One run of `livery_tracker.py` - one update of livery store content. 
I'd recommend to use 1 hour interval between runs.

Env variables required to run updater:

`DB_USERNAME` - username for postgres DB

`DB_PASSWORD` - password for postgres DB

`DB_HOSTNAME` - IP address or domain with postgres DB

`DB_PORT` - port to connect to postgres DB

`DB_DATABASE` - database name to use on postgres DB server

`DISCORD_WEBHOOK_1` - discord webhook url to send notifications, the program will use all env variables that contains `DISCORD_WEBHOOK` so you can state multiple webhooks

## Web
You can run `web.py` using uwsgi or just straight run the file, then it will use `waitress` as wsgi server.

Env variables required to run updater:

`DB_USERNAME` - check description on `Updater` section

`DB_PASSWORD` - check description on `Updater` section

`DB_HOSTNAME` - check description on `Updater` section

`DB_PORT` - check description on `Updater` section

`DB_DATABASE` - check description on `Updater` section
