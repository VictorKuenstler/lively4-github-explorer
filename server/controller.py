import responder
from playhouse.shortcuts import model_to_dict

from server.models import Project

api = responder.API()


@api.route('/project')
def projects(req, resp):
    query = Project.select().limit(1000)

    resp.media = [model_to_dict(project) for project in query.select()]


@api.route('/project/{id}')
def project(req, resp, id):
    project = Project.get(Project.id == id)

    resp.media = model_to_dict(project)
