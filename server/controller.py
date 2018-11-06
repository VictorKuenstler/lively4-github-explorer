import inspect

import responder
from peewee import DoesNotExist, Model
from playhouse.shortcuts import model_to_dict

import server.models as models

api = responder.API()


@api.route('/models')
def model_list(req, resp):
    response = []
    for name, obj in inspect.getmembers(models):
        if inspect.isclass(obj) and issubclass(obj, Model) and obj != Model:
            response.append(name.lower())
    resp.media = response


@api.route('/models/{model_name}')
def model_multiple(req, resp, model_name):
    model_name = model_name.capitalize()
    if hasattr(models, model_name):
        model = getattr(models, model_name)
        if inspect.isclass(model) and issubclass(model, Model) and model != Model:
            query = model.select().limit(1000)
            resp.media = [model_to_dict(item, recurse=False) for item in query]
            return

    resp.status_code = api.status_codes.HTTP_404


@api.route('/models/{model_name}/{id}')
def model_single(req, resp, model_name, id):
    model_name = model_name.capitalize()
    if hasattr(models, model_name):
        model = getattr(models, model_name)
        if inspect.isclass(model) and issubclass(model, Model) and model != Model:
            try:
                item = model.get(model.id == id)
                resp.media = model_to_dict(item, backrefs=True, max_depth=1)
                return
            except (ValueError, DoesNotExist):
                pass

    resp.status_code = api.status_codes.HTTP_404
