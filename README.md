# syllabits-server
Syllabits backend!

- Designed in Python 3.6.1 to ensure compatibility with Graphene.
- The 'SYLLABITS_MODE' environment variable must be set to either 'production' or 'development' to run the server.
- Main application entry point is wsgi.py. passenger_wsgi.py is also provided so app can be used on a Passenger server.