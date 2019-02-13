"""
Exception raised when the expectation given in the request's Expect header field could not be met by at least
one of the inbound servers.
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]


class ExpectationFailedException(RinzlerHttpException):
    """
    ExpectationFailedException
    """
    status_code = 417
    exception_name = "Expectation Failed"
