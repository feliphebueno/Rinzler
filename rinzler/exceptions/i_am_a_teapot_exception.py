"""
I'm a teapot
"""
from rinzler.exceptions import RinzlerHttpException


class IMaTeapotException(RinzlerHttpException):
    """
    IAmATeapotException
    """

    status_code = 418
    exception_name = "I'm a teapot"
