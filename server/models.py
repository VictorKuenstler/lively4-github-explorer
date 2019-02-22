from peewee import CompositeKey, ForeignKeyField, IntegerField, Model, TextField, DateTimeField

from server.database import db
from server.model_register import ModelRegister

mr = ModelRegister()


@mr.add_model
class User(Model):
    login = TextField(unique=True)
    company = TextField()
    state = TextField()
    city = TextField()
    location = TextField()
    created_at = DateTimeField()

    class Meta:
        database = db
        table_name = 'users'


@mr.add_model
class Project(Model):
    url = TextField(unique=True)
    owner = ForeignKeyField(User, backref='projects')
    name = TextField()
    description = TextField()
    forked_from = ForeignKeyField('self', column_name='forked_from', backref='forks')
    created_at = DateTimeField()

    class Meta:
        database = db
        table_name = 'projects'


@mr.add_model
class Commit(Model):
    sha = TextField(unique=True)
    author = ForeignKeyField(User, backref='authored_commits')
    committer = ForeignKeyField(User, backref='commits')
    created_at = DateTimeField()

    class Meta:
        database = db
        table_name = 'commits'


@mr.add_nm
class ProjectCommitRelationship(Model):
    project = ForeignKeyField(Project, backref='commits')
    commit = ForeignKeyField(Commit, backref='projects')

    class Meta:
        database = db
        table_name = 'project_commits'
        primary_key = CompositeKey('project', 'commit')


@mr.add_nm
class CommitRelationship(Model):
    parent = ForeignKeyField(Commit, backref='children')
    child = ForeignKeyField(Commit, column_name='commit_id', backref='parents')

    class Meta:
        database = db
        table_name = 'commit_parents'
        primary_key = CompositeKey('parent', 'child')


@mr.add_model
class Comment(Model):
    commit = ForeignKeyField(Commit, backref='comments')
    author = ForeignKeyField(User, column_name='user_id', backref='comments')
    body = TextField()
    line = IntegerField()
    position = IntegerField()
    created_at = DateTimeField()

    class Meta:
        database = db
        table_name = 'commit_comments'


@mr.add_nm
class ProjectMembers(Model):
    project = ForeignKeyField(Project, column_name='repo_id', backref='members')
    member = ForeignKeyField(User, column_name='user_id', backref='member_projects')

    class Meta:
        database = db
        table_name = 'project_members'
        primary_key = CompositeKey('project', 'member')


@mr.add_nm
class Followers(Model):
    follower = ForeignKeyField(User, backref='follows')
    user = ForeignKeyField(User, backref='follower')

    class Meta:
        database = db
        primary_key = CompositeKey('follower', 'user')


@mr.add_model
class Issue(Model):
    project = ForeignKeyField(Project, column_name='repo_id', backref='issues')
    reporter = ForeignKeyField(User, backref='reported_issues')
    assignee = ForeignKeyField(User, backref='assigned_issues')
    created_at = DateTimeField()

    class Meta:
        database = db
        table_name = 'issues'
