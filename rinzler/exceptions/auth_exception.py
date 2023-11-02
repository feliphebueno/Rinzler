"""
Exception raised when a request fails to authenticate
"""
from rinzler.exceptions import RinzlerHttpException


class AuthException(RinzlerHttpException):
    """
    AuthException
    """

    status_code = 403
    exception_name = "Forbidden"
