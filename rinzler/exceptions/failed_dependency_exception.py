"""
Exception raised when depended on another request and that request failed.
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]


class FailedDependencyException(RinzlerHttpException):
    """
    FailedDependencyException
    """
    status_code = 424
    exception_name = "Failed Dependency"
