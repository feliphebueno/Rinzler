"""
Exception raised when the requested resource(route, file, database record) is no longer available and will not be
available again
"""
from rinzler.exceptions import RinzlerHttpException


class GoneException(RinzlerHttpException):
    """
    GoneException
    """

    status_code = 410
    exception_name = "Gone"
