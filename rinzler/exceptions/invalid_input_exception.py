"""
Exception raised when a body request can not be decode from JSON and/or it's content doesn't match the minimum
specified values by the app
"""
__author__ = "Rinzler<github.com/feliphebueno>"


class InvalidInputException(BaseException):
    """
    InvalidInputException
    """
    pass
