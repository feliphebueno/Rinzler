"""
Exception raised when one or more conditions given in the request header fields evaluated to false when tested on the
server.
"""
from rinzler.exceptions import RinzlerHttpException


class PreconditionFailedException(RinzlerHttpException):
    """
    PreconditionFailedException
    """

    status_code = 412
    exception_name = "Precondition Failed"
