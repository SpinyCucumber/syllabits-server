from flask_jwt_extended import (
    get_current_user,
    create_access_token,
    create_refresh_token,
    set_refresh_cookies,
    verify_jwt_in_request
)
from flask_jwt_extended.exceptions import RevokedTokenError, UserLookupError
from flask_graphql import GraphQLView
from jwt.exceptions import InvalidTokenError
from flask import current_app as app
from . import schema_loader

class Context:
    """
    Request handling context.
    Contains information about each request, such as user.
    """

    user = None
    refresh_requested = False
    
    def verify_identity(self, refresh=False):
        locations = 'cookies' if refresh else None
        # Verify JWT and update user
        # Optional does not handle revoked tokens, which is strange
        try:
            verify_jwt_in_request(optional=True, refresh=refresh, locations=locations)
            self.user = get_current_user()
        except (RevokedTokenError, InvalidTokenError, UserLookupError):
            self.user = None
    
    def create_access_token(self):
        """
        Generates new access token for the current user
        """
        return create_access_token(self.user)
    
    def request_refresh(self):
        """
        Requests a refresh token to be attached to the response
        """
        self.refresh_requested = True

graphql = GraphQLView(graphiql=app.config["ENABLE_GRAPHIQL"])

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_request():
    # Use the access token to discern identity by default
    context = Context()
    context.verify_identity()
    # Dynamically choose schema based on user authentication
    schema = schema_loader.load(context.user)
    response = graphql.dispatch_request(schema=schema, context=context)
    # If a refresh token was requested, create a refresh token
    # for the current user and attach it as a cookie
    if (context.refresh_requested):
        token = create_refresh_token(context.user)
        set_refresh_cookies(response, token)
    return response