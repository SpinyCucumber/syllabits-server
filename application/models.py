from mongoengine import Document, EmbeddedDocument
from mongoengine.fields import (EmailField, EmbeddedDocumentListField, StringField, BooleanField, ReferenceField, IntField)

# Could create a field that wraps string field for block sequences

class Collection(Document):
    meta = {'collection': 'collection'}
    title = StringField()

class PoemLine(EmbeddedDocument):
    text = StringField()
    key = StringField()
    stanza_break = BooleanField(default=False)

class Poem(Document):
    meta = {'collection': 'poem', 'indexes': ['collection']}
    next = ReferenceField('self', required=False)
    prev = ReferenceField('self', required=False)
    index = IntField(required=False)
    collection = ReferenceField(Collection, required=False)
    title = StringField()
    author = StringField()
    lines = EmbeddedDocumentListField(PoemLine)

class User(Document):
    meta = {'collection': 'user'}
    email = EmailField()
    password_hashed = StringField()

class ProgressLine(EmbeddedDocument):
    answer = StringField()

class Progress(Document):
    meta = {'collection': 'progress'}
    user = ReferenceField(User)
    poem = ReferenceField(Poem)
    lines = EmbeddedDocumentListField(ProgressLine)
    finished = BooleanField()
