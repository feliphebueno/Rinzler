"""
Exception raised when a body request is larger than the app is set to process
"""
from rinzler.exceptions import RinzlerHttpException


class ContentTooLargeException(RinzlerHttpException):
    """
    ContentTooLargeException
    """

    status_code = 413
    exception_name = "Payload Too Large"
