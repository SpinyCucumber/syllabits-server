role_to_schema = {}
public_schema = None

def use_public(schema):
    global public_schema
    public_schema = schema

def use_for_role(role, schema):
    role_to_schema[role] = schema

def load(user):
    schema = public_schema
    if user:
        schema = role_to_schema.get(user.role, public_schema)
    return schema

__all__ = ['use_public', 'use_for_role', 'load']