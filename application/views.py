from flask_jwt_extended import current_user, jwt_required
from flask import current_app as app
from .schemas import public_schema, user_schema
from .flask_graphql import DynamicGraphQLView

# Construct GraphQL view
# We choose the schema based on the
# authentication status of the user
def get_schema():
    if current_user: return user_schema
    return public_schema

def get_root_value():
    return current_user

graphql = DynamicGraphQLView.as_view(
    'graphql',
    get_schema=get_schema,
    get_root_value=get_root_value,
    graphiql=app.config["ENABLE_GRAPHIQL"]
)

@app.route('/')
@jwt_required(optional=True)
def handle_request():
    context = {}
    response = graphql(context)
    # TODO Cookie handling
    return response