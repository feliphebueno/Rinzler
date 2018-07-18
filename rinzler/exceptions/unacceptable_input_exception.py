"""
Exception raised when a body request could be parsed normally, but it's contents doesn't satisfies the specified
values by the app
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]


class UnacceptableInputException(RinzlerHttpException):
    """
    UnacceptableInputException
    """
    status_code = 406
    exception_name = "Not Acceptable"
