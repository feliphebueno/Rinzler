"""
Exception raised when the app fails to process the request and due to an error it couldn't handle correctly
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = "Rinzler<github.com/feliphebueno>"


class InternalException(RinzlerHttpException):
    """
    InternalException
    """
    status_code = 500
    exception_name = "Internal Server Error"
