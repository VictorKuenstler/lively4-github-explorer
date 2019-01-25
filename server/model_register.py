from server.common import camel_to_snake


def _relation_other_field(cls, field):
    fields = list(cls._meta.fields.values())
    assert field in fields

    return fields[0] if field is fields[1] else fields[1]


def _relation_other_field_name(cls, field_name):
    field_names = list(cls._meta.fields.keys())
    assert field_name in field_names

    return field_names[0] if field_name == field_names[1] else field_names[1]


class ModelRegister:
    def __init__(self):
        self._models = {}
        self._nm_relations = {}

    def add_model(self, model):
        name = camel_to_snake(model.__name__)

        model._name = name
        model._type = 'model'

        self._models[name] = model
        return model

    def add_nm(self, nm_relation):
        assert len(nm_relation._meta.fields) == 2, 'nm-relationship must contain two fields.'
        for field in nm_relation._meta.fields.values():
            assert field.__class__.__name__ == 'ForeignKeyField'

        name = camel_to_snake(nm_relation.__name__)

        nm_relation._name = name
        nm_relation._type = 'nm_relation'
        nm_relation._other_field = classmethod(_relation_other_field)
        nm_relation._other_field_name = classmethod(_relation_other_field_name)

        self._nm_relations[name] = nm_relation
        return nm_relation


    def __contains__(self, item):
        return item in self._models

    def __getitem__(self, item):
        return self._models[item]

    def keys(self):
        return self._models.keys()

    def values(self):
        return self._models.values()

    def items(self):
        return self._models.items()

    # def model_desc(self, name):
    #     model = self._models[name]
    #     return {'fields': model._fields(), 'relations': model._relations()}

    # @property
    # def model_descs(self):
    #     return {model_name: self.model_desc(model_name) for model_name in self.model_names}

    def query_dict(self, query, depth=0):
        model_name = query._meta.model._name
        model = self._models[model_name]
        # model_desc = self.model_desc(model_name)

        result = {}
        for field_name, field in model._meta.fields.items():
        # for field_name, field_desc in model_desc['fields'].items():
            if field.__class__.__name__ == 'ForeignKeyField':
                continue
            result[field_name] = query.__data__.get(field_name)

        if depth > 0:
            for field_name, field in model._meta.fields.items():
                # n:1
                if field.__class__.__name__ != 'ForeignKeyField':
                    continue
                if query.__data__.get(field_name):
                    relation_query = getattr(query, field_name)
                    result[field_name] = self.query_dict(relation_query, depth - 1)
                else:
                    result[field_name] = None
            for backref, backref_model in model._meta.backrefs.items():
                if backref_model._type == 'model':
                    # 1:n
                    relation_queries = getattr(query, backref.backref)
                    result[backref.backref] = [self.query_dict(relation_query, depth - 1) for relation_query in relation_queries]
                elif backref_model._type == 'nm_relation':
                    # n:m
                    relation_queries = getattr(query, backref.backref)
                    accum = []
                    for relation_query in relation_queries:
                        other_field = backref_model._other_field(backref).name
                        accum.append(self.query_dict(getattr(relation_query, other_field), depth - 1))
                    result[backref.backref] = accum
        return result
