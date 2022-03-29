### syllabits-server ###
Syllabits backend!

- Designed in Python 3.6.1 to ensure compatibility with Graphene. Compatible with Python 3.6.7/8
- The 'SYLLABITS_MODE' environment variable should be set to either 'production' or 'development.' Defaults to 'development,' which should definitely be avoided in a public-facing server.
- In addition, the 'SYLLABITS_SECRET_KEY' environment variable must be set to a secure (random) value!
- For locked-down server environments (like CPanel), the environment variable 'SYLLABITS_PYTHON' is also provided. This can be used to specify the path of the preferred Python interpreter when running as a Passenger app. (Passenger is the application platform that CPanel uses.)
- Main application entry point is the 'application' module. passenger_wsgi.py is the entry point when running as a Passenger app. For more information on installing a Passenger Python app, see https://docs.cpanel.net/knowledge-base/web-services/how-to-install-a-python-wsgi-application/
- The API is entirely GraphQL, and the server only has one endpoint ( '/' ) which is the GraphQL endpoint.

# Development Environment
- A 'launch.json' launch configuration is provided to simplify testing the server in VSCode. In general, you can use the command 'python3 -m flask run' with FLASK_APP=application to run the server.
- The 'launch.json' file provides three launch configurations: 'Syllabits Server,' which allows the backend to be debugged in development mode, 'Syllabits Server (Shell),' which starts the flask shell, and 'Test Server,' which is a minimalist server designed for quickly testing the schema.

# Installing Dependencies
- Dependencies can be installed with 'pip3 install --user -r requirements.txt'