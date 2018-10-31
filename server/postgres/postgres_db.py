import os

import psycopg2
import psycopg2.extras


def get_connection_parameters():
    dbname = os.environ['PSQL_NAME']
    user = os.environ['PSQL_USER']
    password = os.environ['PSQL_PASSWORD']

    return f'dbname={dbname} user={user} password={password}'


class PostgresDb:
    def __init__(self):
        connection_parameters = get_connection_parameters()

        self.connection = psycopg2.connect(connection_parameters)
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)


class PostgresDbConnection:
    def __init__(self):
        self._connection_parameters = get_connection_parameters()

    def __enter__(self):
        self.connection = psycopg2.connect(self._connection_parameters)
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()


class PostgresDbDictCursor(PostgresDbConnection):
    def __init__(self):
        super().__init__()

    def __enter__(self):
        super().__enter__()
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        super().__exit__(exc_type, exc_val, exc_tb)

