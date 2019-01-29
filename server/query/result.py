import peewee

from server.query.builder import QueryCommand


def generate_result_object(query_object, query_tree_node):
    result = {}
    for field_node in query_tree_node.fields:
        if QueryCommand.SELECT in field_node.commands:
            result[field_node.name] = getattr(query_object, field_node.name)
    for child_node in query_tree_node.children:
        if QueryCommand.SELECT in child_node.commands:
            child_object = getattr(query_object, child_node.name)
            if isinstance(child_object, peewee.Model):
                result[child_node.name] = generate_result_object(child_object, child_node)
            elif isinstance(child_object, peewee.SelectQuery) and child_node.shadow_name is None:
                result[child_node.name] = [generate_result_object(child_query, child_node) for child_query in child_object]
            elif isinstance(child_object, peewee.SelectQuery) and child_node.shadow_name is not None:
                result[child_node.name] = [
                    generate_result_object(getattr(child_query, child_node.shadow_name), child_node) for
                    child_query in child_object]
    return result
