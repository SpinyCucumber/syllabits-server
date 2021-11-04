from flask import current_app as app
from flask_graphql import GraphQLView
from flask_jwt_extended import current_user, jwt_required

from .schemas import base_schema, user_schema

user_context = lambda: { 'user': current_user }
base_view = GraphQLView.as_view("base", schema=base_schema, graphiql=app.config["ENABLE_GRAPHIQL"])
user_view = GraphQLView.as_view("user", schema=user_schema, graphiql=app.config["ENABLE_GRAPHIQL"], get_context=user_context)

@app.route('/', methods = ('GET', 'POST', 'PUT', 'DELETE'))
@jwt_required(optional=True)
def root():
    # Base view is default
    view = base_view
    # If user is present, switch to user view
    if (current_user):
        view = user_view
    return view()