class QueryTreeNode:
    def __init__(self, name, model, shadow_name=None, parent=None):
        self.name = name
        self.model = model
        self.shadow_name = shadow_name
        assert parent is None or isinstance(parent, QueryTreeNode)
        self.parent = parent
        if parent is not None:
            parent.children.append(self)
        self.children = []
        self.fields = []
        self.commands = []

    def add_child(self, name, model, shadow_name=None):
        return QueryTreeNode(name, model, shadow_name=shadow_name, parent=self)

    def add_field(self, name, field):
        return QueryTreeFieldNode(name, field, self)

    def get_child(self, name, default=None):
        for child in self.children:
            if child.name == name:
                return child
        return default

    def get_field(self, name, default=None):
        for field in self.fields:
            if field.name == name:
                return field
        return default

    @property
    def is_root(self):
        return self.parent is None

    def __iter__(self):
        yield self
        for field in self.fields:
            yield field
        for child in self.children:
            for c in child:
                yield c

    def __repr__(self):
        return f'QueryTreeNode({self.name}, {self.model}, shadow_name={self.shadow_name})'


class QueryTreeFieldNode:
    def __init__(self, name, field, parent):
        self.name = name
        self.field = field
        assert isinstance(parent, QueryTreeNode)
        self.parent = parent
        parent.fields.append(self)
        self.commands = []

    def __repr__(self):
        return f'QueryTreeFieldNode({self.name}, {self.field})'


class QueryTree:
    def __init__(self, model):
        self.root = QueryTreeNode(model._name, model)

    def node_iter(self):
        for node in self.root:
            yield node

    def field_iter(self):
        for field in self.root:
            if isinstance(field, QueryTreeFieldNode):
                yield field
