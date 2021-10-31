from flask import Flask
from flask_graphql import GraphQLView
from flask_cors import CORS
from mongoengine import connect

def create_app():

    app = Flask(__name__)
    # Enter app context (necessary for creating views and such)
    with app.app_context():

        # Apply CORS
        CORS(app)

        # Initialize configs and load the appropriate one
        from . import configs
        from .config_loader import load_config
        load_config(app.config)

        # Connect to DB
        connect(db=app.config['MONGO_DB'], host=app.config['MONGO_URI'])

        # Construct GraphQL
        from .schema import schema
        app.add_url_rule(
            "/graphql", view_func=GraphQLView.as_view("graphql", schema=schema, graphiql=app.config["ENABLE_GRAPHIQL"])
        )
    
    return app