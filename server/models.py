import os
from peewee import Model, PostgresqlDatabase, TextField

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


class User(Model):
    login = TextField(unique=True, index=True)
    company = TextField()
    state = TextField()
    city = TextField()
    location = TextField

    class Meta:
        database = db
        table_name = 'users'
