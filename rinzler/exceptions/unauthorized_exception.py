"""
Exception raised when a request must be authenticated
"""
from rinzler.exceptions import RinzlerHttpException


class UnauthorizedException(RinzlerHttpException):
    """
    UnauthorizedException
    """

    status_code = 401
    exception_name = "Unauthorized"
