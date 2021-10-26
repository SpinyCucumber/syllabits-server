from flask import Flask

def create_app():

    app = Flask(__name__)
    # Enter app context (necessary for creating views and such)
    with app.app_context():

        # Initialize configs and load the appropriate one
        from . import configs
        from .config_loader import load_config
        load_config(app.config)
        # TODO Construct GraphQL
        pass
    
    return app