"""
Rinzler's exceptions module
:author: Rinzler<github.com/feliphebueno>
:date: 14/07/2018
"""
__author__ = "Rinzler<github.com/feliphebueno>"


class RinzlerHttpException(BaseException):
    """
    Rinzler's base HTTP Exception, all other HTTP Exceptions must subclass this class as well as override it's
    properties status_code and exception_name in order to be properly converted to a HTTP Error Response to the client.
    """
    status_code = 0
    exception_name = "Cataclysmic Error"

    def __int__(self):
        return int(self.status_code)

    def __repr__(self):
        return self.__str__()
