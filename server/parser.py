from pypeg2 import *


class ModelCommand(str):
    grammar = 'MODEL:'

class SelectCommand(str):
    grammar = 'SELECT:'

class GroupCommand(str):
    grammar = 'GROUPBY:'

class OrderCommand(str):
    grammar = 'ORDERBY:'

class WhereCommand(str):
    grammar = 'WHERE:'

class SumAggregator(str):
    grammar = 'SUM:'

class AvgAggregator(str):
    grammar = 'AVG:'

class CountAggregator(str):
    grammar = 'COUNT:'

class MinAggregator(str):
    grammar = 'MIN:'

class MaxAggregator(str):
    grammar = 'MAX:'

class Aggregator:
    grammar = attr('_type', [SumAggregator, AvgAggregator, CountAggregator, MinAggregator, MaxAggregator])

    @property
    def type(self):
        return type(self._type)

class Integer:
    grammar = attr('_value', re.compile(r'-?[1-9][0-9]*'))

    @property
    def value(self):
        return int(self._value)

class String:
    grammar = attr('_value', re.compile(r'(["\'])(?:(?=(\\?))\2.)*?\1'))

    @property
    def value(self):
        return self._value[1:-1]

class Identifier:
    grammar = attr('value', re.compile(r'[a-zA-Z][a-zA-Z0-9_]*'))

class EqComparator(str):
    grammar = '=='

class GeqComparator(str):
    grammar = '>='

class LeqComparator(str):
    grammar = '<='

class GreaterComparator(str):
    grammar = '>'

class LessComparator(str):
    grammar = '<'

class NeqComparator(str):
    grammar = '!='

class Comparator:
    grammar = attr('_type', [EqComparator, GeqComparator, LeqComparator, GreaterComparator, LessComparator, NeqComparator])

    @property
    def type(self):
        return type(self._type)

class AndOperator(str):
    grammar = 'AND'

class OrOperator(str):
    grammar = 'OR'

class XorOperator(str):
    grammar = 'XOR'

class LogicalOperator:
    grammar = attr('_type', [AndOperator, OrOperator, XorOperator])

    @property
    def type(self):
        return type(self._type)

class ModelName:
    grammar = attr('_value', Identifier)

    @property
    def value(self):
        return self._value.value

class FieldName:
    grammar = attr('_values', csl(Identifier, separator='.'))

    @property
    def values(self):
        return [v.value for v in self._values]

class Aggregation:
    grammar = attr('_aggregator', Aggregator), attr('field', FieldName)

    @property
    def aggregator(self):
        return self._aggregator.type

class Comparision:
    grammar = [
        (attr('first', FieldName), attr('_comparator', Comparator), attr('second', FieldName)),
        (attr('first', FieldName), attr('_comparator', Comparator), attr('second', Integer)),
        (attr('first', FieldName), attr('_comparator', Comparator), attr('second', String)),
        (attr('first', Integer), attr('_comparator', Comparator), attr('second', FieldName)),
        (attr('first', String), attr('_comparator', Comparator), attr('second', FieldName))
    ]

    is_comparision = True
    is_logical_expression = False

    @property
    def comparator(self):
        return self._comparator.type

class Expression:
    @property
    def is_comparision(self):
        return hasattr(self, '_comparision') and not hasattr(self, '_helper')

    @property
    def is_logical_expression(self):
        return not self.is_comparision

    @property
    def first(self):
        if self.is_comparision:
            return self._comparision.first
        elif hasattr(self, '_helper'):
            return self._expression
        else:
            return self._expression.first

    @property
    def second(self):
        if self.is_comparision:
            return self._comparision.second
        elif hasattr(self, '_helper'):
            return self._helper.expression
        else:
            return self._expression.second

    @property
    def comparator(self):
        if hasattr(self, '_comparision'):
            return self._comparision.comparator

    @property
    def logical_operator(self):
        if hasattr(self, '_helper'):
            return self._helper.operator.type
        elif hasattr(self, '_expression'):
            return self._expression.logical_operator

class ExpressionHelper:
    pass

Expression.grammar = [
    (attr('_expression', Comparision), attr('_helper', ExpressionHelper)),
    ('(', attr('_expression', Expression), ')', attr('_helper', ExpressionHelper)),
    (attr('_comparision', Comparision), ),
    ('(', attr('_expression', Expression), ')'),
]

ExpressionHelper.grammar = attr('operator', LogicalOperator), attr('expression', Expression)

class Model:
    grammar = ignore(ModelCommand), attr('_name', ModelName)

    @property
    def name(self):
        return self._name.value

class Select(List):
    grammar = ignore(SelectCommand), '(', csl([Aggregation, FieldName]), ')'

class GroupBy(List):
    grammar = ignore(GroupCommand), '(', csl(FieldName), ')'

class OrderBy(List):
    grammar = ignore(OrderCommand), '(', csl(FieldName), ')'

class Where(List):
    grammar = ignore(WhereCommand), attr('expression', Expression)

class Query:
    grammar = attr('model', Model),\
              attr('select', Select),\
              attr('group_by', optional(GroupBy)),\
              attr('order_by', optional(OrderBy)),\
              attr('where', optional(Where))
