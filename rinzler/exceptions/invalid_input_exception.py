"""
Exception raised when a body request can not be decode from JSON and/or it's content doesn't match the minimum
specified values by the app
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = "Rinzler<github.com/feliphebueno>"


class InvalidInputException(RinzlerHttpException):
    """
    InvalidInputException
    """
    status_code = 400
    exception_name = "Bad Request"
