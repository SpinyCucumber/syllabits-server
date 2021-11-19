from flask_jwt_extended import current_user, jwt_required, create_refresh_token, set_refresh_cookies
from flask import current_app as app
from .schemas import public_schema, user_schema
from .flask_graphql import DynamicGraphQLView

"""
Request handling context.
Contains information about each request, such as user.
"""
class Context:

    user = None
    create_refresh_token = False

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

# Construct GraphQL view
# We choose the schema based on the
# authentication status of the user
def get_schema():
    if current_user: return user_schema
    return public_schema
# Use the user as the root value of the schema for convenience
def get_root_value():
    return current_user

graphql = DynamicGraphQLView(
    get_schema=get_schema,
    get_root_value=get_root_value,
    graphiql=app.config["ENABLE_GRAPHIQL"]
)

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required(optional=True)
def handle_request():
    context = Context(user=current_user)
    response = graphql.dispatch_request(context)
    # If graphql requested a refresh token to be created,
    # create a refresh token for the current user and attach it
    # as a cookie
    if (context.create_refresh_token):
        token = create_refresh_token(context.user)
        set_refresh_cookies(response, token)
    return response