from server.common import camel_to_snake


def _model_fields(cls):
    fields = {}
    for field_name, field in cls._meta.fields.items():
        field_type = field.__class__.__name__
        if field_type == 'ForeignKeyField':
            continue
        field_dict = {'type': field_type}
        if field.primary_key:
            field_dict['primary_key'] = True
        if field.unique:
            field_dict['unique'] = True
        fields[field_name] = field_dict
    return fields


def _model_relations(cls):
    relations = {}
    for field_name, field in cls._meta.fields.items():
        field_type = field.__class__.__name__
        if field_type != 'ForeignKeyField':
            continue

        assert hasattr(field.rel_model, '_name')
        assert hasattr(field.rel_model, '_type') and field.rel_model._type == 'model'

        rel_model = field.rel_model._name
        field_dict = {'type': 'rel', 'relationship_type': 'n:1', 'rel_model': rel_model}
        relations[field_name] = field_dict
    for backref, backref_model in cls._meta.backrefs.items():
        assert hasattr(backref_model, '_name')
        assert hasattr(backref_model, '_type')
        assert backref_model._type == 'model' or backref_model._type == 'nm_relationship'

        backref_name = backref_model._name
        backref_type = backref_model._type

        if backref_type == 'model':
            field_dict = {'type': 'rel', 'relationship_type': '1:n', 'rel_model': backref_name}
        else:
            field_dict = {'type': 'rel', 'relationship_type': 'n:m', 'rel_model': backref_model._other(cls._name)}
        relations[backref.backref] = field_dict

    return relations


def _relationship_models(cls):
    return [f.rel_model for f in cls._meta.fields.values()]


def _relationship_model_names(cls):
    return [m._name for m in cls._models()]


def _relationship_other(cls, model):
    if isinstance(model, str):
        model_names = cls._model_names()
        assert model in model_names
        return model_names[1] if model == model_names[0] else model_names[0]
    else:
        models = cls._models()
        assert model in models
        return models[1] if model is models[0] else models[0]


class ModelRegister:
    def __init__(self):
        self._models = {}
        self._nm_relationships = {}

    def add_model(self, model):
        name = camel_to_snake(model.__name__)

        model._name = name
        model._type = 'model'
        model._fields = classmethod(_model_fields)
        model._relations = classmethod(_model_relations)

        self._models[name] = model
        return model

    def add_nm(self, nm_relationship):
        assert len(nm_relationship._meta.fields) == 2, 'nm-relationship must contain two fields.'

        name = camel_to_snake(nm_relationship.__name__)

        nm_relationship._name = name
        nm_relationship._type = 'nm_relationship'
        nm_relationship._models = classmethod(_relationship_models)
        nm_relationship._model_names = classmethod(_relationship_model_names)
        nm_relationship._other = classmethod(_relationship_other)

        self._nm_relationships[name] = nm_relationship
        return nm_relationship

    @property
    def models(self):
        return [model for model in self._models.values()]

    @property
    def model_names(self):
        return [model._name for model in self.models]

    def __contains__(self, item):
        return item in self._models

    def __getitem__(self, item):
        return self._models[item]

    @property
    def model_descriptions(self):
        result = {}
        for model in self.models:
            result[model._name] = {**model._fields(), **model._relations()}
        return result
