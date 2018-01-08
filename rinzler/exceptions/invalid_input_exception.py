"""
Exception raised when a body request can not be decode from JSON and/or it's content doesn't match the minimum
specified values by the app
"""


class InvalidInputException(BaseException):
    """
    InvalidInputException
    """
    pass
