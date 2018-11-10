import os
from peewee import CompositeKey, ForeignKeyField, IntegerField, Model, PostgresqlDatabase, TextField

db_name = os.environ['PSQL_NAME']
user = os.environ['PSQL_USER']
password = os.environ['PSQL_PASSWORD']

db = PostgresqlDatabase(db_name, user=user, password=password)


class User(Model):
    login = TextField(unique=True)
    company = TextField()
    state = TextField()
    city = TextField()
    location = TextField

    class Meta:
        database = db
        table_name = 'users'


class Project(Model):
    url = TextField(unique=True)
    owner = ForeignKeyField(User, backref='projects')
    name = TextField()
    description = TextField()
    forked_from = ForeignKeyField('self', column_name='forked_from', backref='forks')

    class Meta:
        database = db
        table_name = 'projects'


class Commit(Model):
    sha = TextField(unique=True)
    author = ForeignKeyField(User, backref='authored_commits')
    committer = ForeignKeyField(User, backref='commits')

    class Meta:
        database = db
        table_name = 'commits'


class ProjectCommit(Model):
    project = ForeignKeyField(Project, backref='project_commits')
    commit = ForeignKeyField(Commit, backref='project_commits')

    class Meta:
        database = db
        table_name = 'project_commits'
        primary_key = CompositeKey('project', 'commit')


class CommitRelationship(Model):
    parent = ForeignKeyField(Commit, backref='children')
    child = ForeignKeyField(Commit, column_name='commit_id', backref='parents')

    class Meta:
        database = db
        table_name = 'commit_parents'
        primary_key = CompositeKey('parent', 'child')


class Comment(Model):
    commit = ForeignKeyField(Commit, backref='comments')
    author = ForeignKeyField(User, column_name='user_id', backref='comments')
    body = TextField()
    line = IntegerField()
    position = IntegerField()

    class Meta:
        database = db
        table_name = 'commit_comments'
