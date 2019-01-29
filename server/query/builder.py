from enum import Enum

import peewee

from server import parser
from server.query.tree import QueryTree


class QueryBuilder:
    def __init__(self, mr):
        self.mr = mr

        self.used_models = None
        self.query_tree = None
        self.query = None

    def __call__(self, cql_query):
        ### REMOVE used_models, query from self

        self.used_models = []

        parsed_query = parser.parse(cql_query, parser.Query)

        selection_fields = [
            (s.values, None) if isinstance(s, parser.FieldName) else (s.field.values, s.aggregator)
            for s in parsed_query.select
        ]
        group_by_fields = [field.values for field in parsed_query.group_by] if parsed_query.group_by is not None else []
        order_by_fields = [field.values for field in parsed_query.order_by] if parsed_query.order_by is not None else []
        where_fields = self._expression_fields(parsed_query.where.expression) if parsed_query.where is not None else []

        model = self.mr[parsed_query.model.name]
        self.query_tree = QueryTree(model)
        self.used_models.append(model)

        self.query = model.select()

        selections = []
        for field_arr, aggregator in selection_fields:
            selection = self._add_to_node(self.query_tree.root, field_arr, QueryCommand.SELECT)
            if aggregator is None:
                selections.append(selection)
            elif aggregator is parser.SumAggregator:
                selections.append(peewee.fn.Sum(selection).alias('sum'))
            elif aggregator is parser.AvgAggregator:
                selections.append(peewee.fn.Avg(selection).alias('avg'))
            elif aggregator is parser.CountAggregator:
                selections.append(peewee.fn.Count(selection).alias('count'))
            elif aggregator is parser.MinAggregator:
                selections.append(peewee.fn.Min(selection).alias('min'))
            elif aggregator is parser.MaxAggregator:
                selections.append(peewee.fn.Max(selection).alias('max'))

        group_by = [self._add_to_node(self.query_tree.root, field_arr, QueryCommand.GROUPBY) for field_arr in group_by_fields]
        order_by = [self._add_to_node(self.query_tree.root, field_arr, QueryCommand.ORDERBY) for field_arr in order_by_fields]
        # TODO Where

        self.query = self.query\
            .group_by(*group_by)\
            .order_by(*order_by)\
            .limit(1000)

        return self.query, self.query_tree

    @staticmethod
    def _expression_fields(expression):
        if expression.is_logical_expression:
            return QueryBuilder._expression_fields(expression.first) + QueryBuilder._expression_fields(expression.second)
        else:
            first = expression.first.values
            second = expression.second.values if isinstance(expression.second, parser.FieldName) else None
            if second:
                return [first, second]
            else:
                return [first]

    def _add_to_node(self, node, field_arr, query_command):
        field_head, *field_arr = field_arr

        model_fields = node.model._meta.fields
        model_backrefs = {backref.backref: backref for backref in node.model._meta.backrefs.keys()}
        if field_head in model_fields and not isinstance(model_fields[field_head], peewee.ForeignKeyField):
            # field_head is of type field
            assert len(field_arr) == 0, f'Field {field_head} of model {node.model._name} has no children.'
            field_node = node.get_field(field_head)
            if not field_node:
                field_node = node.add_field(field_head, getattr(node.model, field_head))
            if query_command not in field_node.commands:
                field_node.commands.append(query_command)
            return field_node.field
        elif field_head in model_fields and isinstance(model_fields[field_head], peewee.ForeignKeyField):
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
            if query_command not in child_node.commands:
                child_node.commands.append(query_command)
            if len(field_arr) == 0:
                return child_node.model
            return self._add_to_node(child_node, field_arr, query_command)
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
            if query_command not in child_node.commands:
                child_node.commands.append(query_command)
            if len(field_arr) == 0:
                return child_node.model
            return self._add_to_node(child_node, field_arr, query_command)
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
                child_node = node.add_child(field_head, join_model, shadow_name=join_field_2.name)
            if query_command not in child_node.commands:
                child_node.commands.append(query_command)
            if len(field_arr) == 0:
                return child_node.model
            return self._add_to_node(child_node, field_arr, query_command)
        else:
            raise AssertionError(f'Field {field_head} of model {node.model._name} does not exist.')


class QueryCommand(Enum):
    SELECT = 1
    ORDERBY = 2
    GROUPBY = 3
    WHERE = 4
