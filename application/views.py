from flask_jwt_extended import get_current_user, create_refresh_token, set_refresh_cookies, verify_jwt_in_request
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
    
    def verify_identity(self, refresh=False):
        locations = 'cookies' if refresh else None
        verify_jwt_in_request(optional=True, refresh=refresh, locations=locations)
        # Make sure to update user
        self.user = get_current_user()

graphql = DynamicGraphQLView(graphiql=app.config["ENABLE_GRAPHIQL"])

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_request():
    # Use the access token to discern identity by default
    context = Context()
    context.verify_identity()
    # Dynamically choose schema based on authentication
    # Use the user as the root value of the schema for convenience
    schema = user_schema if context.user else public_schema
    response = graphql.dispatch_request(schema, root_value=context.user, context=context)
    # If a refresh token was requested, create a refresh token
    # for the current user and attach it as a cookie
    if (context.create_refresh_token):
        token = create_refresh_token(context.user)
        set_refresh_cookies(response, token)
    return response