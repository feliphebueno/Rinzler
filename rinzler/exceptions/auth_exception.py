"""
Exception raised when a request fails to authenticate
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]


class AuthException(RinzlerHttpException):
    """
    AuthException
    """
    status_code = 403
    exception_name = "Forbidden"
