from server.common import camel_to_snake


def _model_fields(cls):
    fields = []
    for field_name, field in cls._meta.fields.items():
        field_type = field.__class__.__name__
        if field_type == 'ForeignKeyField':
            continue
        field_dict = {'name': field_name, 'type': field_type}
        if field.primary_key:
            field_dict['primary_key'] = True
        if field.unique:
            field_dict['unique'] = True
        fields.append(field_dict)

    return fields


def _model_relations(cls):
    relations = []
    for field_name, field in cls._meta.fields.items():
        field_type = field.__class__.__name__
        if field_type != 'ForeignKeyField':
            continue

        assert hasattr(field.rel_model, '_name')
        assert hasattr(field.rel_model, '_type') and field.rel_model._type == 'model'

        rel_model = field.rel_model._name
        relations.append({'name': field_name, 'type': 'n:1', 'rel_model': rel_model})
    for backref, backref_model in cls._meta.backrefs.items():
        assert hasattr(backref_model, '_name')
        assert hasattr(backref_model, '_type')
        assert backref_model._type == 'model' or backref_model._type == 'nm_relationship'

        backref_name = backref_model._name
        backref_type = backref_model._type

        relation_dict = {'name': backref.backref}
        if backref_type == 'model':
            relation_dict['type'] = '1:n'
            relation_dict['rel_model'] = backref_name
        else:
            relation_dict['type'] = 'n:m'
            relation_dict['rel_model'] = backref_model._other_relation(backref.name)[1]
        relations.append(relation_dict)

    return relations


def _relationship_relations(cls):
    relations = {}
    for field_name, field in cls._meta.fields.items():
        rel_model = field.rel_model._name
        relations[field_name] = rel_model
    return relations


def _relationship_other_relation(cls, relation):
    relations = cls._relations()
    relation_keys = list(relations.keys())
    assert relation in relation_keys

    if relation == relation_keys[0]:
        index = 1
    else:
        index = 0
    return relation_keys[index], relations[relation_keys[index]]


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
        for field in nm_relationship._meta.fields.values():
            assert field.__class__.__name__ == 'ForeignKeyField'

        name = camel_to_snake(nm_relationship.__name__)

        nm_relationship._name = name
        nm_relationship._type = 'nm_relationship'
        nm_relationship._relations = classmethod(_relationship_relations)
        nm_relationship._other_relation = classmethod(_relationship_other_relation)

        self._nm_relationships[name] = nm_relationship
        return nm_relationship

    @property
    def models(self):
        return list(self._models.values())

    @property
    def model_names(self):
        return list(self._models.keys())

    def __contains__(self, item):
        return item in self._models

    def __getitem__(self, item):
        return self._models[item]

    def model_description(self, name):
        model = self._models[name]
        return {'model': model._name, 'fields': model._fields(), 'relations': model._relations()}

    def query_dict(self, query, depth=0):
        model_description = self.model_description(query._meta.model._name)

        result = {}
        for field in model_description['fields']:
            result[field['name']] = query.__data__.get(field['name'])
        if depth > 0:
            for relation_description in model_description['relations']:
                relation_name = relation_description['name']
                relation_type = relation_description['type']
                assert relation_type == 'n:1' or relation_type == '1:n' or relation_type == 'n:m'
                if relation_type == 'n:1':
                    # if reference id is set, load referenced model
                    if query.__data__.get(relation_name):
                        relation_query = getattr(query, relation_name)
                        result[relation_name] = self.query_dict(relation_query, depth - 1)
                    else:
                        result[relation_name] = None
                elif relation_type == '1:n':
                    relation_queries = getattr(query, relation_name)
                    accum = []
                    for relation_query in relation_queries:
                        accum.append(self.query_dict(relation_query, depth - 1))
                    result[relation_name] = accum
                else:
                    relation_queries = getattr(query, relation_name)
                    relation_model_1 = relation_queries._where.lhs.name
                    relation_model_2 = relation_queries.model._other_relation(relation_model_1)[0]
                    accum = []
                    for relation_query in relation_queries:
                        relation_query = getattr(relation_query, relation_model_2)
                        accum.append(self.query_dict(relation_query, depth - 1))
                    result[relation_name] = accum
        return result
