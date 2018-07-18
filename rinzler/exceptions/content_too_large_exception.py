"""
Exception raised when a body request is larger than the app is set to process
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]


class ContentTooLargeException(RinzlerHttpException):
    """
    ContentTooLargeException
    """
    status_code = 413
    exception_name = "Payload Too Large"
