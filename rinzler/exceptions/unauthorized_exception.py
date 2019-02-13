"""
Exception raised when a request must be authenticated
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]


class UnauthorizedException(RinzlerHttpException):
    """
    UnauthorizedException
    """
    status_code = 401
    exception_name = "Unauthorized"
