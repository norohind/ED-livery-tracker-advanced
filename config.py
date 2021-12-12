import os

postgres_username = os.getenv('DB_USERNAME')
postgres_password = os.getenv('DB_PASSWORD')
postgres_hostname = os.getenv('DB_HOSTNAME')
postgres_port = os.getenv('DB_PORT')
postgres_database_name = os.getenv('DB_DATABASE')

discord_webhooks: list[str] = []

for env_var in os.environ:
    if 'DISCORD_WEBHOOK' in env_var:
        discord_webhooks.append(os.environ[env_var])
