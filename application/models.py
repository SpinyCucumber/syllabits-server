from mongoengine import Document, EmbeddedDocument
from mongoengine.fields import (EmailField, EmbeddedDocumentListField, ListField, StringField, BooleanField, ReferenceField, IntField, DateTimeField)

"""
Categories are like "tags" used to describe poems and collections.
Collections are more rigid when compared to categories: they have an order and tend not to change.
Collections are intended to be used for cataloging, assignments, etc.
Categories are used to describe groups of similar poems. For example, a category could describe poems
that share a common theme, were written in the same time period, etc.
"""
class Category(Document):
    meta = {'collection': 'category'}
    name = StringField()
    references = IntField()

class Collection(Document):
    meta = {'collection': 'collection'}
    title = StringField()
    """
    Collections can have categories just like poems.
    """
    categories = ListField(ReferenceField(Category))
    poems = ListField(ReferenceField('Poem'))
    primary = BooleanField(default=False)

class PoemLine(EmbeddedDocument):
    text = StringField()
    key = StringField()
    stanza_break = BooleanField(default=False)

class Poem(Document):
    meta = {'collection': 'poem'}
    categories = ListField(ReferenceField(Category))
    title = StringField()
    author = StringField()
    lines = EmbeddedDocumentListField(PoemLine)
    # These fields are deprecated and will be phased out in favor of "smarter" collection handling
    next = ReferenceField('self')
    prev = ReferenceField('self')
    index = IntField()
    collection = ReferenceField(Collection)

"""
There are several ways to locate a poem.
One way is to directly use the ID of a poem.
Another way is to identity a collection and specify an index.
"""
class PoemLocation(EmbeddedDocument):
    meta = {'allow_inheritance': True}

class DirectionLocation(PoemLocation):
    poem = ReferenceField(Poem)

class CollectionLocation(PoemLocation):
    collection = ReferenceField(Collection)
    index = IntField()

class User(Document):
    meta = {'collection': 'user', 'indexes': ['email']}
    email = EmailField(unique=True)
    is_admin = BooleanField()
    password_hashed = StringField()
    """
    A user can have multiple relationships with a poem, which can overlap, and have
    different rules for transitioning between them.
    A user can 'save' poems. This is a simple, general-purpose feature which allows
    users to remember poems (that they would like to play, for instance)
    When the user starts working on a poem, the poem is moved from saved to in-progress.
    """
    saved = ListField(ReferenceField(Poem))
    """
    A list of the poems the user is currently "working on."
    Important to note is that all poems in-progress have an associated Progress document,
    but the vice-versa isn't necessarily true. A poem can be completed and not in-progress,
    and still have a progress document.
    A poem becomes in-progress by initially submitting a line of the poem.
    """
    in_progress = ListField(ReferenceField(Poem))
    """
    A list of poems the user has completed.
    A poem becomes completed once all lines are correct. Once completed, a poem is no longer
    considered in-progress, but can become in-progress again by resetting the progress.
    """
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

"""
Used to track invalidated tokens
When a user logs out, their token is marked as invalidated, meaning it cannot be
used for future login attempts. Whenever we mark the token as invalidated, we make sure
to include an 'expireAfterSeconds' index of the expires field so that our database isn't
polluted with old tokens.
"""
class TokenBlocklist(Document):
    meta = {
        'collection': 'token_blocklist',
        'indexes': [{'fields': ['expires'], 'expireAfterSeconds': 0}]
    }
    jti = StringField(primary_key=True)
    expires = DateTimeField()
