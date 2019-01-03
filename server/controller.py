import responder
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from server.models import mr

api = responder.API()


@api.route('/models')
def model_list(req, resp):
    resp.media = mr.model_names


@api.route('/models/{model_name}')
def multiple_models(req, resp, model_name):
    model_name = model_name.lower()
    if model_name in mr:
        model = mr[model_name]
        query = model.select().limit(1000)
        resp.media = [model_to_dict(item, recurse=False) for item in query]
    else:
        resp.status_code = api.status_codes.HTTP_404


@api.route('/models/{model_name}/{id_}')
def model_single(req, resp, model_name, id_):
    model_name = model_name.lower()
    if model_name in mr:
        model = mr[model_name]
        try:
            query = model.get(model.id == id_)
            resp.media = mr.query_dict(query, 1)
            return
        except (ValueError, DoesNotExist):
            pass
    resp.status_code = api.status_codes.HTTP_404


@api.route('/meta')
def meta(req, resp):
    resp.media = []
    for model_name in mr.model_names:
        resp.media.append(mr.model_description(model_name))
