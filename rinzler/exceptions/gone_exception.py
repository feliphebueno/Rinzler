"""
Exception raised when the requested resource(route, file, database record) is no longer available and will not be
available again
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]


class GoneException(RinzlerHttpException):
    """
    GoneException
    """
    status_code = 410
    exception_name = "Gone"
