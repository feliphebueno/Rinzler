"""
Exception raised when the origin server requires the request to be conditional.
Intended to prevent the 'lost update' problem, where a client GETs a resource's state, modifies it,
and PUTs it back to the server, when meanwhile a third party has modified the state on the server, leading to a conflict
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]


class PreconditionRequiredException(RinzlerHttpException):
    """
    PreconditionRequiredException
    """
    status_code = 428
    exception_name = "Precondition Required"
