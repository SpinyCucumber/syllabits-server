from flask import current_app as app
from flask_graphql import GraphQLView
from flask_jwt_extended import current_user, jwt_required

from .schemas import base_schema, user_schema

context = lambda: { 'user': current_user }

def create_view(name, schema):
    return GraphQLView.as_view(name, schema=schema, graphiql=app.config["ENABLE_GRAPHIQL"], get_context=context)

base_view = create_view('base', base_schema)
user_view = create_view('user', user_schema)

@app.route('/', methods = ('GET', 'POST', 'PUT', 'DELETE'))
@jwt_required(optional=True)
def root():
    # Base view is default
    view = base_view
    # If user is present, switch to user view
    if (current_user):
        view = user_view
    return view()