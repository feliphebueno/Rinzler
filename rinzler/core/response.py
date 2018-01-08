"""
Interface for HttpResponse
"""
import json
from collections import OrderedDict
from django.http.response import HttpResponse


class Response(object):
    """
    Response
    """
    __content = OrderedDict
    __content_type = str()
    __charset = str()
    __kwargs = dict
    __indent = 0

    def __init__(self, content, content_type="application/json", charset="utf-8", **kwargs):
        """
        Constructor
        :param content str conteúdo da resposta
        :param content_type str content-type da resposta
        :param kwargs dict
        :rtype: None
        """
        self.__content = content
        self.__content_type = content_type
        self.__charset = charset
        self.__kwargs = kwargs

    def render(self, indent=0):
        """
        Renders a HttpResponse for the ongoing request
        :param indent int
        :rtype: HttpResponse
        """
        self.__indent = indent
        return HttpResponse(
            self.__str__(), content_type=self.__content_type, charset=self.__charset, **self.__kwargs
        )

    def __str__(self):
        if self.__indent > 0:
            if self.__content is not None:
                return json.dumps(self.__content, indent=self.__indent, sort_keys=False)
            else:
                return str()
        else:
            if self.__content is not None:
                return json.dumps(self.__content, sort_keys=False)
            else:
                return str()

    def __repr__(self):
        return self.__str__()

    def get_decoded(self):
        """
        Returns a decoded instance of this object
        :rtype: object
        """
        return json.loads(self.__content)
