class InsufficientPrivilegeError(Exception):
    """
    Raised when accessing a field that the user is not authorized to access
    Ex. non-admin accessing poem keys
    """
    pass