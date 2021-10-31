import click
import json
from flask import current_app
from .models import Collection, Poem

@current_app.cli.command('import-collection')
@click.argument('path', type=click.Path(exists=True))
@click.argument('title')
def importcollection(path, title):
    click.echo(f'Importing collection \'{path}\'...')

    with open(path) as file:
        data = json.load(file)

        # Create new collection
        collection = Collection(title=title)
        collection.save()

        index = 0
        prev_poem = None
        for poem_data in data:
            # Create new poem and link to collection/other poems
            poem = Poem._from_son(poem_data, created=True)
            poem.collection = collection
            poem.index = index
            poem.save()

            if (prev_poem):
                poem.prev = prev_poem
                prev_poem.next = poem
                poem.save()
                prev_poem.save()

            # Increment index
            index += 1
            prev_poem = poem
        
        click.echo('Done')
        


