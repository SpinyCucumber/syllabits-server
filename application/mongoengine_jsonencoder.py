# Credit to https://gist.github.com/corydolphin/11005158#file-mongoengine_jsonencoder-py

from flask import Flask
from flask.json import JSONEncoder
from bson import json_util
from mongoengine.base import BaseDocument
from mongoengine.queryset.base import BaseQuerySet

class MongoEngineJSONEncoder(JSONEncoder):
    def default(self,obj):
        if isinstance(obj,BaseDocument):
            return json_util._json_convert(obj.to_mongo())
        elif isinstance(obj,BaseQuerySet):
            return json_util._json_convert(obj.as_pymongo())
        elif isinstance(obj,ObjectId):
            # TODO
            pass

        return JSONEncoder.default(self, obj)