"""
Exception raised when the App tries to comunicate with third-party online services and this comunications fails
"""
from rinzler.exceptions import RinzlerHttpException


class ServiceUnavailableException(RinzlerHttpException):
    """
    ServiceUnavailableException
    """

    status_code = 503
    exception_name = "Service Unavailable"
