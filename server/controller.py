import responder
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict


from server.models import mr
from server.query.builder import QueryBuilder
from server.query.result import generate_result_object

api = responder.API()


@api.route('/models')
def model_list(req, resp):
    resp.media = list(mr.keys())


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
    for model_name, model in mr.items():
        model_meta = {'model': model_name, 'fields': [], 'relations': []}
        for field_name, field in model._meta.fields.items():
            field_type = field.__class__.__name__
            if field_type == 'ForeignKeyField':
                continue
            field_dict = {'name': field_name, 'type': field_type}
            if field.primary_key:
                field_dict['primary_key'] = True
            if field.unique:
                field_dict['unique'] = True
            model_meta['fields'].append(field_dict)

        for field_name, field in model._meta.fields.items():
            field_type = field.__class__.__name__
            if field_type != 'ForeignKeyField':
                continue

            assert hasattr(field.rel_model, '_name')
            assert hasattr(field.rel_model, '_type') and field.rel_model._type == 'model'

            rel_model = field.rel_model._name
            model_meta['relations'].append({'name': field_name, 'type': 'n:1', 'rel_model': rel_model})
        for backref, backref_model in model._meta.backrefs.items():
            assert hasattr(backref_model, '_name')
            assert hasattr(backref_model, '_type')
            assert backref_model._type == 'model' or backref_model._type == 'nm_relation'

            backref_name = backref_model._name
            backref_type = backref_model._type

            relation_dict = {'name': backref.backref}
            if backref_type == 'model':
                relation_dict['type'] = '1:n'
                relation_dict['rel_model'] = backref_name
            else:
                relation_dict['type'] = 'n:m'
                relation_dict['rel_model'] = backref_model._other_field(backref).rel_model._name
            model_meta['relations'].append(relation_dict)

        resp.media.append(model_meta)


@api.route('/dummy')
def dummy(req, resp):
    r = [
        {
            'sha': 'f0df88fd2775f37e023ad628ec7d35a082394b6b',
            'author': {
                'login': 'userdummy',
                'company': 'companydummy',
            },
            'comments': [
                {
                    'body': 'comment1',
                    'line': 1,
                    'position': 10,
                },
                {
                    'body': 'comment2',
                    'line': 5,
                    'position': 12,
                },
                {
                    'body': 'comment3',
                    'line': 3,
                    'position': 1,
                }
            ],
            'children': [],
        },
        {
            'sha': 'abc88fd2775f37e023ad628ec7d35a082394b6a',
            'author': {
                'login': 'anon',
                'company': None,
            },
            'comments': [
                {
                    'body': 'comment4',
                    'line': 1,
                    'position': 1
                }
            ],
            'children': [
                {
                    'sha': 'def88fd2775f37e023ad628ec7d35a082394b6a',
                },
                {
                    'sha': 'ghi88fd2775f37e023ad628ec7d35a082394b6a',
                },
                {
                    'sha': 'jkl88fd2775f37e023ad628ec7d35a082394b6a',
                },
            ]   
        }
    ]

    print(r)

    resp.media = r


@api.route('/query')
def query(req, resp):
    if 'q' not in req.params:
        return
    cql_query = req.params['q']
    query_builder = QueryBuilder(mr)
    query, query_tree = query_builder(cql_query)

    resp.media = [generate_result_object(row, query_tree.root) for row in query]
