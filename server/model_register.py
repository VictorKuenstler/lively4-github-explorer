from server.common import camel_to_snake


class ModelRegister:
    def __init__(self):
        self.models = {}
        self.nm_relationships = {}

    def add_model(self, model):
        name = camel_to_snake(model.__name__)
        self.models[name] = model
        return model

    def add_nm(self, nm_relationship):
        self.nm_relationships[nm_relationship.__name__] = nm_relationship
        return nm_relationship

    @property
    def model_names(self):
        return list(self.models.keys())
