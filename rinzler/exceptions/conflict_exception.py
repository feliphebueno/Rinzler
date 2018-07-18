"""
Exception raised when the theres a conflict in the request, such as an edit conflict between multiple simultaneous
updates
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]


class ConflictException(RinzlerHttpException):
    """
    ConflictException
    """
    status_code = 409
    exception_name = "Conflict"
