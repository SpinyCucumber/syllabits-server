from enum import Enum

class Role(str, Enum):
    """
    SyllaBits uses a simple role-based permission system.
    Each role owns a set of permissions, which is accessed using the 'perms' property.
    Roles can inherit permissions from other roles which allows for a role hierarchy.
    An individual permission can be tested for using the 'has_perm' method.
    """
    # I chose to implement roles using an enum rather than something more class-based so that it
    # can be used directly as a Mongoengine field.

    def __new__(cls, value, options={}):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._has = set(options.get('has', []))
        obj._inherits = options.get('inherits', [])
        return obj
    
    @property
    def perms(self):
        # Cache the role perms as perms are tested often
        if hasattr(self, '_perms'):
            return self._perms
        perms = self._has.copy()
        for parent in self._inherits:
            # Dereference parent and combine permissions
            perms = perms.union(Role[parent].perms)
        self._perms = perms
        return perms
    
    def has_perm(self, perm):
        return (perm in self.perms)
    
    USER = ('u', {'has': ['basic1', 'basic2']})
    EDITOR = ('e', {'has': ['secret1'], 'inherits': ['USER']})
    ADMIN = ('a', {'has': ['super_secret1'], 'inherits': ['EDITOR']})