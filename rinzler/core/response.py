import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http.response import HttpResponse


class Response:
    """
    Interface for HttpResponse
    """

    __content = {}
    __content_type = ""
    __charset = ""
    __kwargs = {}
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

    @property
    def status_code(self) -> int:
        """
        HTTP status code this response will carry once rendered.

        Exposed because consumers legitimately need the status *before*
        `render()` is called — the response callback, for one, receives this
        object from `Router.dispatch` while it is still a Response and not yet
        an HttpResponse. Without this property the only way to reach the status
        was `response._Response__kwargs`, and reading a name-mangled attribute
        across package boundaries is how it eventually broke.

        The default mirrors HttpResponse's own: no explicit status means 200.
        :rtype: int
        """
        return self.__kwargs.get("status", 200)

    def render(self, indent=0):
        """
        Renders a HttpResponse for the ongoing request
        :param indent int
        :rtype: HttpResponse
        """
        self.__indent = indent
        return HttpResponse(str(self), content_type=self.__content_type, charset=self.__charset, **self.__kwargs)

    def __str__(self):
        if self.__indent > 0:
            if self.__content is not None:
                return json.dumps(
                    self.__content,
                    indent=self.__indent,
                    sort_keys=False,
                    cls=DjangoJSONEncoder,
                )
            else:
                return ""
        else:
            if self.__content is not None:
                return json.dumps(self.__content, sort_keys=False, cls=DjangoJSONEncoder)
            else:
                return ""

    def __repr__(self):
        return self.__str__()

    def get_decoded(self):
        """
        Returns a decoded instance of this object
        :rtype: object
        """
        return json.loads(self.__content)
