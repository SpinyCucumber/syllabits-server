from blinker import signal

pre_create = signal('pre_create')
"""
Sent by MongoengineCreateMutation before saving the created document
"""

pre_delete = signal('pre_delete')
"""
Sent by MongoengineDeleteMutation before deleting the document
"""

pre_update = signal('pre_update')
"""
Sent by MongoengineUpdateMutation before applying a transform to the document
Provides the operator, the receiver, and the arguments
"""