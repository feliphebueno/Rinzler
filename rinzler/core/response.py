import json
from collections import OrderedDict
from django.http.response import HttpResponse
from django.utils.datastructures import OrderedSet


class Response(object):

    __content = OrderedDict
    __content_type = str()
    __kwargs = dict
    __indent = 0

    def __init__(self, content, content_type="text/html", **kwargs):
        self.__content = OrderedDict(content)
        self.__content_type = content_type
        self.__kwargs = kwargs

    def render(self, indent=0):
        self.__indent = indent
        return HttpResponse(self.__str__(), content_type=self.__content_type, **self.__kwargs)

    def __str__(self):
        return json.dumps(OrderedDict(self.__content), indent=self.__indent, sort_keys=False)

    def __repr__(self):
        return self.__str__()

    def get_decoded(self):
        return json.loads(self.__content)
