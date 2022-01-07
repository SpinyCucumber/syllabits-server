import json
import base64
from .types import CountableConnection, MongoengineCreateMutation, MongoengineUpdateMutation
from .document_path import DocumentPath

def find_conflicts(key, answer):
    """
    Finds differences between a submitted answer and a key
    Assumes the answer and the key are the same length
    Returns a list of indicies of differences
    """
    # Compare the blocks one-by-one: if there is a mismatch, record the index.
    conflicts = []
    assert len(key) == len(answer)
    for i in range(len(key)):
        if (key[i] != answer[i]):
            conflicts.append(i)
    return conflicts

def decode_location(location):
    return json.loads(base64.b64decode(location))

def encode_location(location):
    return base64.b64encode(json.dumps(location))

__all__ = [
    'DocumentPath',
    'CountableConnection',
    'MongoengineCreateMutation',
    'MongoengineUpdateMutation',
    'find_conflicts',
    'decode_location',
    'encode_location',
]
