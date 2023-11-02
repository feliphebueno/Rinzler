"""
Exception raised when the requested resource(route, file, database record) could not be found
"""
from rinzler.exceptions import RinzlerHttpException


class NotFoundException(RinzlerHttpException):
    """
    NotFoundException
    """

    status_code = 404
    exception_name = "Not Found"
