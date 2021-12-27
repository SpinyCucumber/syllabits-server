import click
import json
from flask import current_app
from .models import Poem

@current_app.cli.command('importpoems')
@click.argument('path', type=click.Path(exists=True))
def import_poems(path):
    click.echo(f'Importing poems from \'{path}\'...')

    with open(path) as file:
        data = json.load(file)

        for poem_data in data:
            # Create new poem
            poem = Poem._from_son(poem_data, created=True)
            poem.save()
        
        click.echo('Done')
        


