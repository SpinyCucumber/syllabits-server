import click
import json
from flask import current_app
from .models import Collection, Poem

@current_app.cli.command('import-collection')
@click.argument('path', type=click.Path(exists=True))
@click.argument('title')
def import_collection(path, title):

    with open(path) as file:
        data = json.load(file)

        # Create new collection
        collection = Collection(title=title)

        index = 0
        prev_poem = None
        poems = []
        for poem_data in data:
            # Create new poem and link to collection/other poems
            poem = Poem.from_json(poem_data, created=True)
            poem.collection = collection
            poem.index = index
            if (prev_poem):
                poem.prev = prev_poem
                prev_poem.next = poem
            # Increment index
            index += 1
            prev_poem = poem
            poems.append(poem)
        
        # Save all poems and collection
        for poem in poems: poem.save()
        collection.save()
        


