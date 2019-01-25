from peewee import ForeignKeyField, fn
from playhouse.shortcuts import model_to_dict

from server.parser import *


class QueryBuilder:
    def __init__(self, cql_query, mr):
        self.cql_query = cql_query
        self.mr = mr

        self.used_models = []

        parsed_query = parse(self.cql_query, Query)
        selection_fields = [
            (s.values, None) if isinstance(s, FieldName) else (s.field.values, s.aggregator)
            for s in parsed_query.select
        ]
        group_by_fields = [field.values for field in parsed_query.group_by] if parsed_query.group_by is not None else []
        order_by_fields = [field.values for field in parsed_query.order_by] if parsed_query.order_by is not None else []
        where_fields = self._expression_fields(parsed_query.where.expression) if parsed_query.where is not None else []


        model = mr[parsed_query.model.name]
        query_tree = QueryTreeNode(model._name, model=model)
        self.used_models.append(model)

        self.query = model.select()

        selections = []
        for field_arr, aggregator in selection_fields:
            selection = self._add_to_node(query_tree, field_arr)
            if aggregator is None:
                selections.append(selection)
            elif aggregator is SumAggregator:
                selections.append(fn.Sum(selection).alias('sum'))
            elif aggregator is AvgAggregator:
                selections.append(fn.Avg(selection).alias('avg'))
            elif aggregator is CountAggregator:
                selections.append(fn.Count(selection).alias('count'))
            elif aggregator is MinAggregator:
                selections.append(fn.Min(selection).alias('min'))
            elif aggregator is MaxAggregator:
                selections.append(fn.Max(selection).alias('max'))

        group_by = [self._add_to_node(query_tree, field_arr) for field_arr in group_by_fields]
        order_by = [self._add_to_node(query_tree, field_arr) for field_arr in order_by_fields]
        # TODO Where

        # overwrite query
        self.query = self.query.group_by(*group_by)
        self.query = self.query.order_by(*order_by)

        self.query = (self.query.select(*selections).limit(1000))


    @staticmethod
    def _expression_fields(expression):
        if expression.is_logical_expression:
            return QueryBuilder._expression_fields(expression.first) + QueryBuilder._expression_fields(expression.second)
        else:
            first = expression.first.values
            second = expression.second.values if isinstance(expression.second, FieldName) else None
            if second:
                return [first, second]
            else:
                return [first]

    def _add_to_node(self, node, field_arr):
        field_head, *field_arr = field_arr

        model_fields = node.model._meta.fields
        model_backrefs = {backref.backref: backref for backref in node.model._meta.backrefs.keys()}
        if field_head in model_fields and not isinstance(model_fields[field_head], ForeignKeyField):
            # field_head is of type field
            assert len(field_arr) == 0, f'Field {field_head} of model {node.model._name} has no children.'
            if field_head not in node.fields:
                node.fields.append(field_head)
            return getattr(node.model, field_head)
        elif field_head in model_fields and isinstance(model_fields[field_head], ForeignKeyField):
            # field_head is of type relation n:1
            child_node = node.get_child(field_head)
            if not child_node:
                field = model_fields[field_head]
                join_model = field.rel_model
                if join_model not in self.used_models:
                    self.used_models.append(join_model)
                else:
                    join_model = join_model.alias()
                self.query = self.query.join_from(node.model, join_model, on=(field == getattr(join_model, join_model._meta.primary_key.name)))
                child_node = node.add_child(field_head, join_model)
            if len(field_arr) == 0:
                return child_node.model
            return self._add_to_node(child_node, field_arr)
        elif field_head in model_backrefs and model_backrefs[field_head].model._type == 'model':
            # field_head is of type relation 1:n
            child_node = node.get_child(field_head)
            if not child_node:
                join_model = model_backrefs[field_head].model
                if join_model not in self.used_models:
                    self.used_models.append(join_model)
                else:
                    join_model = join_model.alias()
                join_field = getattr(join_model, model_backrefs[field_head].name)
                self.query = self.query.join_from(node.model, join_model, on=(join_field))
                child_node = node.add_child(field_head, join_model)
            if len(field_arr) == 0:
                return child_node.model
            return self._add_to_node(child_node, field_arr)
        elif field_head in model_backrefs and model_backrefs[field_head].model._type == 'nm_relation':
            # field_head is of type relation n:m
            child_node = node.get_child(field_head)
            if not child_node:
                join_field_1 = model_backrefs[field_head]
                join_relation = model_backrefs[field_head].model
                join_field_2 = join_relation._other_field(join_field_1)
                join_model = join_field_2.rel_model
                if join_relation not in self.used_models:
                    self.used_models.append(join_relation)
                else:
                    join_relation = join_relation.alias()
                    join_field_1 = getattr(join_relation, join_field_1.name)
                    join_field_2 = getattr(join_relation, join_field_2.name)
                if join_model not in self.used_models:
                    self.used_models.append(join_model)
                else:
                    join_model = join_model.alias()
                self.query = self.query.join_from(node.model, join_relation, on=(join_field_1))
                self.query = self.query.join_from(join_relation, join_model, on=(join_field_2 == getattr(join_model, join_model._meta.primary_key.name)))
                child_node = node.add_child(field_head, join_model)
            if len(field_arr) == 0:
                return child_node.model
            return self._add_to_node(child_node, field_arr)
        else:
            raise AssertionError(f'Field {field_head} of model {node.model._name} does not exist.')


class QueryTreeNode:
    def __init__(self, name, parent=None, model=None):
        self.name = name
        assert parent is None or isinstance(parent, QueryTreeNode)
        self.parent = parent
        if parent is not None:
            parent.children.append(self)
        self.children = []
        self.fields = []
        self.model = model

    def add_child(self, name, model=None):
        return QueryTreeNode(name, parent=self, model=model)

    def get_child(self, name, default=None):
        for child in self.children:
            if child.name == name:
                return child
        return default

    @property
    def is_root(self):
        return self.parent is None

    @property
    def is_leaf(self):
        return len(self.children) == 0

    def __iter__(self):
        yield self
        for child in self.children:
            for c in child:
                yield c

    def __repr__(self):
        name = self.name
        node = self
        while not node.is_root:
            name = node.parent.name + '/' + name
            node = node.parent
        return f'QueryTreeNode({name}, model={self.model}, fields={self.fields})'
