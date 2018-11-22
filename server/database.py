import os

from peewee import PostgresqlDatabase

db_name = os.environ['PSQL_NAME']
user = os.environ['PSQL_USER']
password = os.environ['PSQL_PASSWORD']

db = PostgresqlDatabase(db_name, user=user, password=password)
