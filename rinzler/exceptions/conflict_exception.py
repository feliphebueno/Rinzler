"""
Exception raised when the theres a conflict in the request, such as an edit conflict between multiple simultaneous
updates
"""
from rinzler.exceptions import RinzlerHttpException


class ConflictException(RinzlerHttpException):
    """
    ConflictException
    """

    status_code = 409
    exception_name = "Conflict"
