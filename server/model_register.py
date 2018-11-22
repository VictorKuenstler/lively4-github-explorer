from server.common import camel_to_snake


class ModelRegister:
    def __init__(self):
        self._models = {}
        self._nm_relationships = {}

    def add_model(self, model):
        name = camel_to_snake(model.__name__)
        self._models[name] = model
        return model

    def add_nm(self, nm_relationship):
        self._nm_relationships[nm_relationship.__name__] = nm_relationship
        return nm_relationship

    @property
    def model_names(self):
        return list(self._models.keys())

    def __contains__(self, item):
        return item in self._models

    def __getitem__(self, item):
        return self._models[item]
