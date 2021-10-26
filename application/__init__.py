from flask import Flask
from flask_graphql import GraphQLView

def create_app():

    app = Flask(__name__)
    # Enter app context (necessary for creating views and such)
    with app.app_context():

        # Initialize configs and load the appropriate one
        from . import configs
        from .config_loader import load_config
        load_config(app.config)

        # Construct GraphQL
        from .schema import schema
        app.add_url_rule(
            "/graphql", view_func=GraphQLView.as_view("graphql", schema=schema, graphiql=True)
        )
    
    return app