"""
Exception raised when the theres a conflict in the request, such as an edit conflict between multiple simultaneous
updates
"""
__author__ = "Rinzler<github.com/feliphebueno>"


class ConflictException(BaseException):
    """
    ConflictException
    """
    pass
