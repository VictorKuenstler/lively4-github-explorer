import os

from peewee import PostgresqlDatabase, Model, CharField, TextField

dbname = os.environ['PSQL_NAME']
user = os.environ['PSQL_USER']
password = os.environ['PSQL_PASSWORD']

db = PostgresqlDatabase(dbname, user=user, password=password)


class Project(Model):
    url = TextField()
    name = TextField()
    description = TextField()

    class Meta:
        database = db
        table_name = 'projects'
