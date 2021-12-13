import typing

import psycopg2.extensions
import psycopg2.extras
import config

from . import postgres_sql_requests
from .abstract_model import AbstractModel


def errors_catcher(func: callable) -> callable:
    def decorated(*args, **kwargs):
        try:
            result = func(*args, **kwargs)

        except psycopg2.InterfaceError:
            args[0].open_model()
            result = func(*args, **kwargs)

        return result

    return decorated


class PostgresModel(AbstractModel):
    db: psycopg2.extensions.connection

    def open_model(self):
        self.db: psycopg2.extensions.connection = psycopg2.connect(
            user=config.postgres_username,
            password=config.postgres_password,
            host=config.postgres_hostname,
            port=config.postgres_port,
            database=config.postgres_database_name,
            cursor_factory=psycopg2.extras.DictCursor)

        # print(f'Connected to {self.db.dsn}')

        with self.db:
            with self.db.cursor() as cursor:
                cursor.execute(postgres_sql_requests.schema_create)  # schema creation

    def close_model(self):
        self.db.close()
        # print(f'Connection to {self.db.dsn} closed successfully')

    @errors_catcher
    def get_activity_changes(self, limit: int, low_timestamp, high_timestamp) -> list:

        with self.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(postgres_sql_requests.select_activity_pretty_names, {
                'limit': limit,
                'high_timestamp': high_timestamp,
                'low_timestamp': low_timestamp
            })

            result: list = cursor.fetchall()

        return result

    @errors_catcher
    def insert_livery(self, livery_list: list) -> int:
        """
        Takes livery content as list insert to DB

        :param livery_list: list from get_onlinestore_data
        :return:
        """

        action_id: int  # not last, current that we will use

        with self.db.cursor() as cursor:
            cursor.execute(postgres_sql_requests.select_last_action_id)
            action_id_fetch_one: typing.Union[None, dict[str, int]] = cursor.fetchone()

        if action_id_fetch_one is None:
            # i.e. first launch
            action_id = 1  # yep, not 0

        else:
            action_id = action_id_fetch_one['action_id'] + 1

        # Patch for additional values
        for squad in livery_list:
            squad.update({'action_id': action_id})

        with self.db:
            with self.db.cursor() as cursor:
                cursor.executemany(
                    postgres_sql_requests.insert_livery,
                    livery_list)

        return action_id

    @errors_catcher
    def insert_livery_timestamp(self, livery_list: list) -> int:
        """
        Takes livery content with timestamps as list insert to DB. Helpful for historical data

        :param livery_list: list from get_onlinestore_data
        :return:
        """

        action_id: int  # not last, current that we will use

        with self.db.cursor() as cursor:
            cursor.execute(postgres_sql_requests.select_last_action_id)
            action_id_fetch_one: typing.Union[None, dict[str, int]] = cursor.fetchone()

        if action_id_fetch_one is None:
            # i.e. first launch
            action_id = 1  # yep, not 0

        else:
            action_id = action_id_fetch_one['action_id'] + 1

        # Patch for additional values
        for squad in livery_list:
            squad.update({'action_id': action_id})

        with self.db:
            with self.db.cursor() as cursor:
                cursor.executemany(
                    postgres_sql_requests.insert_livery_timestamp,
                    livery_list)

        return action_id

    @errors_catcher
    def get_diff_action_id(self, action_id: int) -> list:
        """
        Takes action_id and returns which squadrons has been changed in leaderboard as in action_id and
        experience they got in compassion to action_id - 1 for the same leaderboard and platform

        :param action_id:
        :return:
        """

        with self.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(postgres_sql_requests.select_diff_by_action_id, {'action_id': action_id})
            result: list = cursor.fetchall()

        return result
