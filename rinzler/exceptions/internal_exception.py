"""
Exception raised when the app fails to process the request and due to an error it couldn't handle correctly
"""
from rinzler.exceptions import RinzlerHttpException


class InternalException(RinzlerHttpException):
    """
    InternalException
    """

    status_code = 500
    exception_name = "Internal Server Error"
