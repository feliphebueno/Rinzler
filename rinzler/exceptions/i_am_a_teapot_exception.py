"""
I'm a teapot
"""
from rinzler.exceptions import RinzlerHttpException

__author__ = ["4ndr<github.com/4ndr>"]


class IMaTeapotException(RinzlerHttpException):
    """
    IAmATeapotException
    """
    status_code = 418
    exception_name = "I'm a teapot"
