from mongoengine import Document, EmbeddedDocument
from bson.objectid import ObjectId
from mongoengine.fields import (
    ObjectIdField,
    EmailField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
    ListField,
    StringField,
    BooleanField,
    ReferenceField,
    IntField,
    DateTimeField,
    MapField,
)

class Category(Document):
    """
    Categories are like "tags" used to describe poems and collections.
    Collections are more rigid when compared to categories: they have an order and tend not to change.
    Collections are intended to be used for cataloging, assignments, etc.
    In other words, collections are more "curated"
    Categories are used to describe groups of similar poems. For example, a category could describe poems
    that share a common theme, were written in the same time period, etc.
    """
    meta = {'collection': 'category'}
    name = StringField(primary_key=True)
    ref_count = IntField(required=True)

class Collection(Document):
    meta = {'collection': 'collection'}
    title = StringField()
    categories = ListField(ReferenceField(Category))
    """
    Collections can have categories just like poems.
    """
    poems = ListField(ReferenceField('Poem'), required=True)
    primary = BooleanField(default=False)

class PoemLine(EmbeddedDocument):
    id = ObjectIdField(primary_key=True, default=ObjectId)
    """
    Each poem line has a unique ID. This gives lines a persistent "name" so we can avoid referencing them by
    index, which is volatile as lines can be created and destroyed.
    """
    order = IntField(required=True)
    """
    We impose a "virtual ordering" on the poem lines to allow them to be rearranged easily.
    The virtual ordering happens all client-side.
    """
    text = StringField(required=True)
    # TODO Allow null
    key = ListField(StringField(max_length=1), required=True)
    """
    The line key is an array of characters where each character corresponds to a type of foot.
    """
    stanza_break = BooleanField(default=False)

class Poem(Document):
    meta = {
        'collection': 'poem',
        # We define a text index for searching poems using content, title, etc.
        'indexes': [
            {
                'fields': ['$title', '$author', '$lines.text'],
                'default_language': 'english',
                'weights': {'title': 10, 'author': 10, 'lines.text': 2}
            }
        ]
    }
    categories = ListField(StringField())
    """
    Each poem can belongs to zero or many categories.
    This list contains the name of each category.
    """
    title = StringField(required=True)
    author = StringField()
    lines = EmbeddedDocumentListField(PoemLine)

    # For testing
    def add_category(self, name):
        if (name not in self.categories):
            Category.objects(name=name).upsert_one(inc__ref_count=1)
            self.modify(push__categories=name)

class User(Document):
    meta = {'collection': 'user', 'indexes': ['email']}
    email = EmailField(unique=True)
    is_admin = BooleanField(default=False)
    password_hashed = StringField(required=True)
    saved = ListField(ReferenceField(Poem))
    """
    A user can 'save' poems. This is a simple, general-purpose feature which allows
    users to remember poems (that they would like to play, for instance)
    When the user starts working on a poem, the poem is moved from saved to in-progress.
    """
    in_progress = ListField(ReferenceField(Poem))
    """
    A list of the poems the user is currently "working on"
    Important to note is that all poems in-progress have an associated Progress document,
    but the vice-versa isn't necessarily true. A poem can be completed and not in-progress,
    and still have a progress document.
    A poem becomes in-progress by initially submitting a line of the poem.
    """
    completed = ListField(ReferenceField(Poem))
    """
    A list of poems the user has completed
    A poem becomes completed once all lines are correct. Once completed, a poem is no longer
    considered in-progress, but can become in-progress again by resetting the progress.
    """
    locations = MapField(StringField())
    """
    A map of poems to locations which were most recently used to access the poem
    """

class ProgressLine(EmbeddedDocument):
    answer = ListField(StringField(max_length=1), required=True)
    correct = BooleanField(required=True)

class Progress(Document):
    meta = {'collection': 'progress', 'indexes': [('user', 'poem')]}
    user = ReferenceField(User, required=True)
    poem = ReferenceField(Poem, required=True, unique_with='user')
    lines = MapField(EmbeddedDocumentField(ProgressLine), required=True)
    num_correct = IntField()

class TokenBlocklist(Document):
    """
    Used to track invalidated tokens
    When a user logs out, their token is marked as invalidated, meaning it cannot be
    used for future login attempts. Whenever we mark the token as invalidated, we make sure
    to include an 'expireAfterSeconds' index of the expires field so that our database isn't
    polluted with old tokens.
    """
    meta = {
        'collection': 'token_blocklist',
        'indexes': [{'fields': ['expires'], 'expireAfterSeconds': 0}]
    }
    jti = StringField(primary_key=True)
    expires = DateTimeField(required=True)
