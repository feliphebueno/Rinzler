"""
Exception raised when a request is made using a HTTP Method not allowed
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]


class NotAllowedException(RinzlerHttpException):
    """
    NotAllowedException
    """
    status_code = 405
    exception_name = "Method Not Allowed"
