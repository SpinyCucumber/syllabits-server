"""
A stripped-down server for testing the app schema.
"""
from flask import Flask
from mongoengine import connect
from flask_graphql import GraphQLView
from application.schemas import admin_schema

def create_app():
    app = Flask(__name__)

    with app.app_context():
        # Connect to DB
        connect(db='syllabits', host='mongodb://127.0.0.1:27017')
        # Create GraphQL view
        app.add_url_rule('/', view_func=GraphQLView.as_view('graphql', schema=admin_schema, graphiql=True))
    
    return app