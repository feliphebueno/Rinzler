"""
Exception raised when the requested resource(route, file, database record) could not be found
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = ["Rinzler<github.com/feliphebueno>", "4ndr<github.com/4ndr>"]


class NotFoundException(RinzlerHttpException):
    """
    NotFoundException
    """
    status_code = 404
    exception_name = "Not Found"
    level = "debug"

    def __init__(self, *args, **kwargs):
        if "level" in kwargs:
            self.level = kwargs["level"]
        super(NotFoundException, self).__init__(*args)
