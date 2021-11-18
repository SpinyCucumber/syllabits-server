from mongoengine import Document, EmbeddedDocument
from mongoengine.fields import (EmailField, EmbeddedDocumentListField, ListField, StringField, BooleanField, ReferenceField, IntField)

# Could create a field that wraps string field for block sequences

class Collection(Document):
    meta = {'collection': 'collection'}
    title = StringField()

class Tag(Document):
    meta = {'collection': 'tag'}
    name = StringField()
    references = IntField()

class PoemLine(EmbeddedDocument):
    text = StringField()
    key = StringField()
    stanza_break = BooleanField(default=False)

class Poem(Document):
    meta = {'collection': 'poem', 'indexes': ['collection']}
    # Next, prev, index and collection are only present are in a single, ordered collection.
    next = ReferenceField('self', required=False)
    prev = ReferenceField('self', required=False)
    index = IntField(required=False)
    collection = ReferenceField(Collection, required=False)
    tags = ListField(ReferenceField(Tag))
    title = StringField()
    author = StringField()
    lines = EmbeddedDocumentListField(PoemLine)

class User(Document):
    meta = {'collection': 'user', 'indexes': ['email']}
    email = EmailField(unique=True)
    is_admin = BooleanField()
    password_hashed = StringField()
    # A user can have multiple relationships with a poem, which can overlap, and have
    # different rules for transitioning between them.
    # A user can 'save' poems. This is a simple, general-purpose feature which allows
    # users to remember poems (that they would like to play, for instance)
    # When the user starts working on a poem, the poem is moved from saved to in-progress.
    saved = ListField(ReferenceField(Poem))
    # A list of the poems the user is currently "working on."
    # Important to note is that all poems in-progress have an associated Progress document,
    # but the vice-versa isn't necessarily true. A poem can be completed and not in-progress,
    # and still have a progress document.
    # A poem becomes in-progress by initially submitting a line of the poem.
    in_progress = ListField(ReferenceField(Poem))
    # A list of poems the user has completed.
    # A poem becomes completed once all lines are correct. Once completed, a poem is no longer
    # considered in-progress, but have become in-progress again by resetting the progress.
    completed = ListField(ReferenceField(Poem))

class ProgressLine(EmbeddedDocument):
    answer = StringField()
    correct = BooleanField()

class Progress(Document):
    meta = {'collection': 'progress', 'indexes': [('user', 'poem')]}
    user = ReferenceField(User)
    poem = ReferenceField(Poem)
    lines = EmbeddedDocumentListField(ProgressLine)
    num_correct = IntField()
