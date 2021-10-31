import click
from flask import current_app

@current_app.cli.command('import-collection')
@click.argument('file')
def import_collection(file):
    # TEST
    print(file)