import pytest

from server.parser import *


def test_integer():
    integer = parse('-123', Integer).value
    assert type(integer) is int
    assert integer == -123

def test_string():
    string = parse('"teststring"', String).value
    assert type(string) is str
    assert string == 'teststring'

    assert parse('"test  string"', String).value == 'test  string'
    assert parse("'test  string'", String).value == 'test  string'

def test_identifier():
    parse('abc', Identifier)
    parse('abc2', Identifier)
    parse('Abc', Identifier)
    parse('AbcAbc', Identifier)
    with pytest.raises(SyntaxError):
        parse('1abc', Identifier)
    with pytest.raises(SyntaxError):
        parse('abc.abc', Identifier)

def test_model_name():
    parse('abc', ModelName)
    parse('abc2', ModelName)
    parse('Abc', ModelName)
    parse('AbcAbc', ModelName)
    with pytest.raises(SyntaxError):
        parse('1abc', ModelName)
    with pytest.raises(SyntaxError):
        parse('abc.abc', ModelName)

def test_field_name():
    field_name = parse('abc', FieldName)
    assert field_name.values == ['abc']
    field_name = parse('abc.def', FieldName)
    assert field_name.values == ['abc', 'def']
    field_name = parse('abc.def.ghi', FieldName)
    assert field_name.values == ['abc', 'def', 'ghi']
    with pytest.raises(SyntaxError):
        parse('abc,def', FieldName)

def test_aggregator():
    assert parse('SUM:', Aggregator).type is SumAggregator
    assert parse('AVG:', Aggregator).type is AvgAggregator
    assert parse('COUNT:', Aggregator).type is CountAggregator
    assert parse('MIN:', Aggregator).type is MinAggregator
    assert parse('MAX:', Aggregator).type is MaxAggregator
    with pytest.raises(SyntaxError):
        parse('SUM', Aggregator)
    with pytest.raises(SyntaxError):
        parse('ABC:', Aggregator)

def test_aggregation():
    aggregation = parse('SUM: field1.field2', Aggregation)
    assert aggregation.aggregator is SumAggregator
    assert type(aggregation.field) is FieldName
    assert aggregation.field.values[0] == 'field1'
    assert aggregation.field.values[1] == 'field2'

def test_comparator():
    assert parse('==', Comparator).type is EqComparator
    assert parse('<=', Comparator).type is LeqComparator
    assert parse('>=', Comparator).type is GeqComparator
    assert parse('<', Comparator).type is LessComparator
    assert parse('>', Comparator).type is GreaterComparator
    assert parse('!=', Comparator).type is NeqComparator

def test_comparision():
    parse('abc == abc', Comparision)
    parse('abc <= "test string"', Comparision)
    parse('abc != 1', Comparision)
    parse('\'test string\' > abc', Comparision)
    parse('12 < abc', Comparision)

    comparision = parse('model.abc != "test_string"', Comparision)
    assert comparision.comparator is NeqComparator
    assert comparision.first.values == ['model', 'abc']
    assert comparision.second.value == 'test_string'

def test_logical_operator():
    assert parse('AND', LogicalOperator).type is AndOperator
    assert parse('OR', LogicalOperator).type is OrOperator
    assert parse('XOR', LogicalOperator).type is XorOperator

def test_expression():
    parse('test == abc', Expression)
    parse('((test == abc))', Expression)
    parse('test.test.test <= test.test', Expression)
    parse('test.test >= abc AND abc.test.test == abc', Expression)

    expression = parse('test.test >= abc AND abc.test.test == abc OR abc == abc', Expression)
    assert expression.is_logical_expression
    assert expression.logical_operator is AndOperator
    assert expression.first.is_comparision
    assert expression.first.comparator is GeqComparator
    assert expression.first.first.values == ['test', 'test']
    assert expression.first.second.values == ['abc']
    assert expression.second.is_logical_expression
    assert expression.second.logical_operator is OrOperator
    assert expression.second.first.is_comparision
    assert expression.second.first.comparator is EqComparator
    assert expression.second.first.first.values == ['abc', 'test', 'test']
    assert expression.second.first.second.values == ['abc']
    assert expression.second.second.is_comparision
    assert expression.second.second.comparator is EqComparator
    assert expression.second.second.first.values == ['abc']
    assert expression.second.second.second.values == ['abc']

    expression = parse('test.test >= abc AND (abc.test.test == abc OR abc == abc)', Expression)
    assert expression.is_logical_expression
    assert expression.logical_operator is AndOperator
    assert expression.first.is_comparision
    assert expression.first.comparator is GeqComparator
    assert expression.first.first.values == ['test', 'test']
    assert expression.first.second.values == ['abc']
    assert expression.second.is_logical_expression
    assert expression.second.logical_operator is OrOperator
    assert expression.second.first.is_comparision
    assert expression.second.first.comparator is EqComparator
    assert expression.second.first.first.values == ['abc', 'test', 'test']
    assert expression.second.first.second.values == ['abc']
    assert expression.second.second.is_comparision
    assert expression.second.second.comparator is EqComparator
    assert expression.second.second.first.values == ['abc']
    assert expression.second.second.second.values == ['abc']


    expression = parse('(test.test >= abc AND abc.test.test == abc) OR abc == abc', Expression)
    assert expression.is_logical_expression
    assert expression.logical_operator is OrOperator
    assert expression.first.is_logical_expression
    assert expression.first.logical_operator is AndOperator
    assert expression.first.first.is_comparision
    assert expression.first.first.comparator is GeqComparator
    assert expression.first.first.first.values == ['test', 'test']
    assert expression.first.first.second.values == ['abc']
    assert expression.first.second.is_comparision
    assert expression.first.second.comparator is EqComparator
    assert expression.first.second.first.values == ['abc', 'test', 'test']
    assert expression.first.second.second.values == ['abc']
    assert expression.second.is_comparision
    assert expression.second.comparator is EqComparator
    assert expression.second.first.values == ['abc']
    assert expression.second.second.values == ['abc']

    expression = parse('abc.test == abc AND ((abc.test <= abc OR abc2.test2 >= abc) OR test.abc == abc)', Expression)
    assert expression.is_logical_expression
    assert expression.logical_operator is AndOperator
    assert expression.first.is_comparision
    assert expression.first.comparator is EqComparator
    assert expression.second.is_logical_expression
    assert expression.second.logical_operator is OrOperator
    assert expression.second.first.is_logical_expression
    assert expression.second.first.logical_operator is OrOperator
    assert expression.second.first.first.is_comparision
    assert expression.second.first.first.comparator is LeqComparator
    assert expression.second.first.first.first.values == ['abc', 'test']
    assert expression.second.first.first.second.values == ['abc']
    assert expression.second.first.second.is_comparision
    assert expression.second.first.second.comparator is GeqComparator
    assert expression.second.first.second.first.values == ['abc2', 'test2']
    assert expression.second.first.second.second.values == ['abc']
    assert expression.second.second.is_comparision
    assert expression.second.second.comparator is EqComparator
    assert expression.second.second.first.values == ['test', 'abc']
    assert expression.second.second.second.values == ['abc']

def test_model():
    model = parse('MODEL: model', Model)
    assert model.name == 'model'

def test_select():
    select = parse('SELECT: (field1, field1.field2, field1.field2.field3, MIN: field4)', Select)
    assert select[0].values[0] == 'field1'
    assert select[1].values[0] == 'field1'
    assert select[1].values[1] == 'field2'
    assert select[2].values[0] == 'field1'
    assert select[2].values[1] == 'field2'
    assert select[2].values[2] == 'field3'
    assert select[3].aggregator is MinAggregator
    assert select[3].field.values == ['field4']

def test_group_by():
    group_by = parse('GROUPBY: (field1, field1.field2)', GroupBy)
    assert group_by[0].values == ['field1']
    assert group_by[1].values == ['field1', 'field2']

    with pytest.raises(SyntaxError):
        parse('GROUPBY: (field1, SUM: field2)', GroupBy)

def test_order_by():
    order_by = parse('ORDERBY: (field1, field1.field2)', OrderBy)
    assert order_by[0].values == ['field1']
    assert order_by[1].values == ['field1', 'field2']

    with pytest.raises(SyntaxError):
        parse('ORDERBY: (field1, SUM: field2)', OrderBy)

def test_where():
    where = parse('WHERE: abc <= "test"', Where)
    assert where.expression.first.values[0] == 'abc'
    assert where.expression.second.value == 'test'
    where = parse('WHERE: (abc == 1) AND (abc.def <= "test")', Where)
    assert where.expression.first.first.values == ['abc']
    assert where.expression.first.second.value == 1
    assert where.expression.second.first.values == ['abc', 'def']
    assert where.expression.second.second.value == 'test'

def test_query():
    query_str = '''
    MODEL: modelname
    SELECT: (
        abc,
        field2,
        abc.field3,
        SUM: field.field
        )
    GROUPBY: (
        field2.abc2 )
    ORDERBY: (
        field2 )
    WHERE: abc <= "asfd" AND (abc.field != 2)
    '''

    query = parse(query_str, Query)
    assert query.model.name == 'modelname'
    assert len(query.select) == 4
    assert query.select[0].values == ['abc']
    assert query.select[1].values == ['field2']
    assert query.select[2].values == ['abc', 'field3']
    assert query.select[3].aggregator is SumAggregator
    assert query.select[3].field.values == ['field', 'field']
    assert len(query.group_by) == 1
    assert query.group_by[0].values == ['field2', 'abc2']
    assert len(query.order_by) == 1
    assert query.order_by[0].values == ['field2']
    assert query.where.expression.is_logical_expression
    assert query.where.expression.first.is_comparision

    query_str = '''
        MODEL: modelname
        SELECT: (
            abc,
            field2,
            abc.field3,
            SUM: field.field
            )
        GROUPBY: (
            field2.abc2 )
        WHERE: abc.abc == def OR ((abc <= "asfd") AND (abc.field != 2))
        '''

    query = parse(query_str, Query)
    assert query.order_by is None
