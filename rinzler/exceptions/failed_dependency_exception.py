"""
Exception raised when depended on another request and that request failed.
"""
from rinzler.exceptions import RinzlerHttpException


class FailedDependencyException(RinzlerHttpException):
    """
    FailedDependencyException
    """

    status_code = 424
    exception_name = "Failed Dependency"
