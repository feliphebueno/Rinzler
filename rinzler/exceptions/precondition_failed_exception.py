"""
Exception raised when one or more conditions given in the request header fields evaluated to false when tested on the
server.
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]


class PreconditionFailedException(RinzlerHttpException):
    """
    PreconditionFailedException
    """
    status_code = 412
    exception_name = "Precondition Failed"
