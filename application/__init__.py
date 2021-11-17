from flask import Flask
from flask_jwt_extended import current_user, jwt_required
from mongoengine import connect
import os

from .flask_graphql import DynamicGraphQLView
from .schemas import public_schema, user_schema

VAR_SECRET_KEY = 'SYLLABITS_SECRET_KEY'

def create_app():

    app = Flask(__name__)
    # Enter app context (necessary for creating views and such)
    with app.app_context():

        # Initialize extensions
        from .extensions import all
        for ext in all: ext.init_app(app)

        # Initialize configs and load the appropriate one
        from . import configs
        from .config_loader import load_config
        load_config(app.config)

        # Load secret key
        secret_key = os.environ.get(VAR_SECRET_KEY)
        if not secret_key:
            print(f'{VAR_SECRET_KEY} must be set!')
            return None
        app.config['JWT_SECRET_KEY'] = secret_key

        # Set up commands
        from . import commands

        # Connect to DB
        connect(db=app.config['MONGO_DB'], host=app.config['MONGO_URI'])

        # Construct view and connect to URL
        def get_context():
            return { 'user': current_user }
        def get_schema():
            if current_user: return user_schema
            return public_schema
        view = jwt_required(optional=True)(DynamicGraphQLView.as_view(
            'root',
            get_schema=get_schema,
            get_context=get_context,
            graphiql=app.config["ENABLE_GRAPHIQL"]
        ))
        app.add_url_rule('/', view_func=view)

    
    return app