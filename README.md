# Github Explorer Server
_Victor Künstler & Friedrich Schöne_

## Abstract
Datasets are growing quickly but at the same time, data scientists create analyses that get more and more complex. Typically, exploring data involves a broad collection of different technologies, tools and it also requires several steps do extract interesting insights. For that reason, the process of building such a workflow until the actual exploration requires a lot of implementation time which often consists of the same steps which requires background knowledge about the data and programming skills.
To reduce this implementation overhead and the need for background knowledge, we developed a tool to explore the data schema, query the data and explore the resulting data visually for a database containing GitHub data (e.g. commits, projects, authors, comments). We abstracted the data and the relations between tables with the help of an ORM.
To support the exploration of the schemata, we developed a custom query language, which, in contrast to traditional SQL, supports a more natural way of exploring data and handling relationships between data.
We extended a code editor to suggest completions and provide examples for different fields and relations based on the preceding selections.
We also provide a data preview that let the user quickly review his or her query results. For the last step, the visualization, we implemented a tool that lets the user visualize the data. This tool allows to configure the data used by the individual visualizations but at the same time does not limit the user on preconfigured visualization.

## Overview
- [Setup](#setup)
- [ORM and Model Register](#orm-and-model-register)
- [Query Builder](#query-builder)
- [Custom Query Language](#custom-query-language)
- [HTTP Server](#http-server)

## Setup
In order to setup the server, install `pipenv` with `python3 -m pip install pipenv`.

Create a virtual python environment and install the pipenv requirements using `pipenv install`.

Enter the virtual environment with: `pipenv shell`.

In order to connect to the database and open the desired port for the webserver create a `.env` file in the project root folder and define the following environment variables:
- `PORT`: Defines the port the webserver should listen to.
- `PSQL_NAME`: Name of the postgres database.
- `PSQL_USER`: User name for the postgres database.
- `PSQL_PASSWORD`: User password for the postgres database.

Start the server with: `python .`

## ORM and Model Register
For the database communication and querying we used the ORM [peewee](http://docs.peewee-orm.com/en/latest/).
We decided on using an ORM in order to simplify query results and handle objects instead of tuple list.

Peewee used python classes to map tables onto objects.
It also comes with the possibility to [auto generate](http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#pwiz) these classes.
_We decided against this auto generation_ mainly because the database tables of the github database are faulty and need human control.

For example the table `commits` has a column named `project_id` which is an foreign key on the `projects` table from which it can be inferred that projects and commits have a 1..n relationship which is untrue since commits can be part of multiple projects. In reality they have a n..m relationship which is represented in the table `project_commits`.

For the later abstraction and the automatic joins we have to save models and the n..m relations (which are models in the ORM as well). We do this in the class `server.model_register.ModelRegister`.
We add the models to the register with python decorators. Models are added with the decorator `ModelRegister.add_model` and n..m relationships with the decorator `ModelRegister.add_nm`.
In addition to adding to the register, we add additional information to the models or n..m relationships.
These are a name in snake case which is generated from the camel case name and the type (model or n..m relationship).

## Query Builder
The query builder (`server.query.builder.QueryBuilder`) uses the query sent by the user (see [CQL](#custom-query-language)) and the model register to generate a peewee query which then can be executed and from which a response object can be generated. The challenge was to join the correct tables automatically.

The main algorithm of the query builder generates a directed tree using the different models from the sent query. Each node of the tree contains a selected model and the edges of the tree represent the joins. The root node of this tree contains the initial model from the query.  
Models which are possible candidates for a join are displayed as children in the query and in the response. E.g. `model1.model2`. Suppose we already have a node with `model1`. For each join we determine one of three cases:
- _n..1 relationship_: We create a child node for the `model1` node which contains `model2`. We join `model1` with `model2` on `model1.<model2_id>` and `model2.<prim_key>`.
- _1..n relationship_: We create a child node for the `model1` node which contains `model2`. We join `model1` with `model2` on `model1.<prim_key>` and `model2.<model1_id>`.
- _n..n relationship_: We have a additional table, we will assume is called `nm` and represents the relationship. In truth `model1.model2` should be `model1.nm.model2`. We create a child node for the `model1` node which contains `model2`. We join `model1` with `nm` on `model1.<prim_key>` and `nm.<model1_id>` and we join `nm` with `model2` on `nm.<model2_id>` and `model2.<prim_key>`.

Note that in the code for building the tree, i.e., the method `_add_to_node` contains some code duplicates that were necessary for comprehensibility.

## Custom Query Language
For querying we decided on creating our own query language called _Custom Query Language (CQL)_.
The language is defined using a _[Parsing Expression Grammar (PEG)](https://en.wikipedia.org/wiki/Parsing_expression_grammar)_ which is common for programming language definitions since it allows linear parsing and has an unique parsing tree which is necessary for the determinism of an algorithm.

In order to parse the grammar we used the parsing framework [pyPEG](https://fdik.org/pyPEG/).

### Definition
The grammar definition is the following:

##### Main Commands
```
<ModelCommand>       ::= 'MODEL:'
<SelectCommand>      ::= 'SELECT:'
<GroupCommand>       ::= 'GROUPBY:'
<OrderCommand>       ::= 'ORDERBY:'
<WhereCommand>       ::= 'WHERE:'
```
##### Aggregation Commands:
```
<SumAggregator>      ::= 'SUM:'
<AvgAggregator>      ::= 'AVG:'
<CountAggregator>    ::= 'COUNT:'
<MinAggregator>      ::= 'MIN:'
<MaxAggregator>      ::= 'MAX:'
<Aggregator>         ::= <SumAggregator> | <AvgAggregator> | <CountAggregator> | <MinAggregator> | <MaxAggregator>
```
##### Basic Types
```
<Integer>            ::= -?[1-9][0-9]*
<String>             ::= (["'])(?:(?=(\\?))\2.)*?\1
<Identifier>         ::= [a-zA-Z][a-zA-Z0-9_]*
```
##### Comparators
```
<EqComparator>       ::= '=='
<GeqComparator>      ::= '>='
<LeqComparator>      ::= '<='
<GreaterComparator>  ::= '>'
<LessComparator>     ::= '<'
<NeqComparator>      ::= '!='
<Comparator>         ::= <EqComparator> | <GeqComparator> | <LeqComparator> | <GreaterComparator> | <LessComparator> | <NeqComparator>
```
##### Operators
```
<AndOperator>        ::= 'AND'
<OrOperator>         ::= 'OR'
<XorOperator>        ::= 'XOR'
<LogicalOperator>    ::= <AndOperator> | <OrOperator> | <XorOperator>
```
##### Seperators
```
<LeftBracket>        ::= '('
<RightBracket>       ::= ')'
<Dot>                ::= '.'
<Comma>              ::= ','
```
##### Grammar
```
<ModelName>          ::= <Identifier>
<FieldName>          ::= <Identifier> (<Dot> <Identifier>)*

<Aggregation>        ::= <Aggregator> <FieldName>

<Comparision>        ::= <FieldName> <Comparator> <FieldName> | <FieldName> <Comparator> <Integer> | <FieldName> <Comparator> <String> | <Integer> <Comparator> <FieldName> | <String> <Comparator> <FieldName>
<Expression>         ::= <Comparision> | <LeftBracket> <Expression> <RightBracket> | <Expression> <LogicalOperator> <Expression>

<Model>              ::= <ModelCommand> <ModelName>
<Select>             ::= <SelectCommand> <LeftBracket> (<FieldName> | <Aggregation>) (<Comma> (<FieldName> | <Aggregation>))* <RightBracket>
<GroupBy>            ::= <GroupCommand> <LeftBracket> <FieldName> (<Comma> <FieldName>)* <RightBracket>
<OrderBy>            ::= <OrderCommand> <LeftBracket> <FieldName> (<Comma> <FieldName>)* <RightBracket>
<Where>              ::= <WhereCommand> <Expression>

<Query>              ::= <Model> <Select> <GroupBy>? <OrderBy>? <Where>?
```

The definition is implemented in `server.parser.py`.

### Example Query
```
MODEL: commit
SELECT: (
	id,
	sha,
	children.id,
	children.sha,
	author.login
	)
WHERE: author.login >= 'a' AND author.login <= 'b'
```

### Left Recursion
A common problem with PEGs is left recursion which can lead to a recursive loop. It happens if there exists a nonterminal that can derive to a sentential form with itself as the leftmost symbol, e.g., `<Nonterminal> ::= <Nonterminal> 'some string' | 'a'`.
Luckily any left recursive grammar can be rewritten to a non left recursive grammar. Unfortunately this will change the parsing tree.

In our case the left recursion happened for the expression definition, i.e. `<Expression> ::= <Comparision> | <LeftBracket> <Expression> <RightBracket> | <Expression> <LogicalOperator> <Expression>`.
We solved it by changing it to the following rules:
```
<Expression>         ::= <Comparision> <ExpressionHelper>? | <LeftBracket> <Expression> <RightBracket> <ExpressionHelper>?
<ExpressionHelper>   ::= <LogicalOperator> <Expression>
```

We solved the problem of the changed parsing tree by adding `@property` decorators to helper functions within the grammar classes which acted as fields.

## HTTP Server
