from flask import Flask

def create_app():

    app = Flask(__name__, instance_relative_config=True)
    # Enter app context (necessary for creating views and such)
    with app.app_context():

        # TODO Construct GraphQL
        pass
    
    return app