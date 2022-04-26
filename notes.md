## Mongoengine Behavior Notes ##
- When saving a ReferenceField, the value must be a document, a DBRef, or an ObjectId.
- When creating a Document with a duplicate ID, Mongoengine by default overwrites the Document with the actual ID when saving.
- cascade_save and save(..., cascade=True) are broken and their behavior must be implemented by overriding save...
    (see https://github.com/MongoEngine/mongoengine/issues/1236)
- If you reload a document with a reference containing a value that hasn't actually been saved, it is replaced with a DBRef.
- The 'with_id' method can be used to retrieve a document with a specific primary key.

## Database Migrations ##
- For migrating from the early permissions sysytem ('is_admin') to the newer, role-based system:
    1. You can delete all 'is_admin' fields using the command

        db.user.update({}, {$unset: {is_admin:1}}, false, true)
    